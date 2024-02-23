from flask import session, redirect
from sqlalchemy import Table, Column, MetaData, Integer, String, Boolean, ForeignKey, create_engine, insert, select, update, exists
from sqlalchemy.dialects.sqlite import TIME, DATE
from datetime import datetime, timezone
import json
from functools import wraps
import logging
from typing import List, Dict

def logged_in(f):
    @wraps(f)
    def inner(*args,  **kwargs):
        if session.get("user") is None:
            return redirect("/login")
        if not session["user"].get("color"):
            return redirect("/user-profile")
        else:
            return f(*args,  **kwargs)
    return inner

engine = None

metadata = MetaData()

users = Table(
    "users", 
    metadata,
    Column("id", Integer, primary_key=True),
    Column("username", String(30)), #uniqute constraint
    Column("password", String),
    Column("color", String)
)

mails = Table(
    "mails",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("text", String),
    Column("sender", ForeignKey("users.id"), nullable=False),
    Column("receiver", ForeignKey("users.id"), nullable=False),
    Column("date", DATE),
    Column("time", TIME(storage_format="%(hour)02d:%(minute)02d:%(second)02d")),   
    Column("read", Boolean, default=False)
)



class Email:
    _engine = None

    @classmethod
    def all_for(cls, receiver_id=None, sender_id=None) -> List[Dict]:
        # Pass any one of the above kwargs
        
        # Query to return all mails with the same sender or receiver
        query = select(mails, users).where(mails.c.receiver==receiver_id).join(users, mails.c.sender==users.c.id) #default for same receiver
        if sender_id:
            query = select(mails, users).where(mails.c.sender==sender_id).join(users, mails.c.receiver==users.c.id)
        stmt = query.order_by(mails.c.date.desc(), mails.c.time.desc()).limit(50)

        emails = []
        with cls.engine.connect() as conn:
            result = conn.execute(stmt)
            for row in result: 
                mail = {
                    "mail_id": row.id,
                    "message": row.text,
                    "receiver": row.receiver,
                    "sender": row.sender,
                    "date": row.date,
                    "time": row.time,
                    "date": row.date,
                    "read": row.read
                }       
                if receiver_id:
                    mail["sender"] = (row.sender, row.username, row.color)
                elif sender_id:
                    mail["receiver"] = (row.receiver, row.username, row.color)
                emails.append(mail)
            return emails
        

    @classmethod
    def is_read(self, mail_id, user_id):
        stmt = update(mails).values(read=True).where(mails.c.id == mail_id, mails.c.receiver == user_id)
        with self.engine.begin() as conn:
            conn.execute(stmt)

    def __init__(self, message, sender, receiver, date=None, time=None, **data):
        self.message = message
        self.sender = sender
        self.receiver = receiver
        self.date = date
        self.time = time
        if not date:
            crnt_tm = datetime.now(timezone.utc)
            self.date = crnt_tm.date()
        if not time:
            self.time = crnt_tm.time()
        for key in data:
            setattr(self, key, data[key])

    def set(self):
        with self.engine.begin() as conn:
            stmt = insert(mails).values(text=self.message, sender=self.sender, receiver=self.receiver, date=self.date, time=self.time)            
            conn.execute(stmt)

            sender = conn.execute(select(users.c.username).where(users.c.id == self.sender)).scalar()
            receiver = conn.execute(select(users.c.username).where(users.c.id == self.receiver)).scalar()
            logging.info(f"Email sent from {sender.title()} to {receiver.title()}")
        
    @property
    def engine(cls):
        print("class property is used")
        if cls._engine == None:
            raise ValueError("Missing Engine")
        else:
            return cls._engine     

    @engine.setter
    def engine(cls, eng):
        cls._engine = eng


def myjson(python_mails):
    json_mails = json.dumps(python_mails, default=str, indent=2)
    return json_mails

if __name__ == "__main__":
    print("Metadata was called")
    metadata.create_all(engine)