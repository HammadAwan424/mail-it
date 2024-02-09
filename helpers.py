from flask import session, redirect
from sqlalchemy import Table, Column, MetaData, Integer, String, Boolean, ForeignKey, create_engine, insert, select, update, exists
from sqlalchemy import or_, and_
from sqlalchemy.dialects.sqlite import TIME, DATE
from datetime import datetime
import logging

def login(f):
    def inner(*args,  **kwargs):
        if session.get("id") is None:
            return redirect("/login")
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

def engine_checker(obj):
    if obj.engine == None:
        raise ValueError("Missing Engine")
    else:
        return obj.engine

class Email:

    engine = None

    @classmethod
    def set_engine(cls, engine):
        cls.engine = engine

    @classmethod
    def all(cls, user_receiver=None, user_sender=None):
        '''Pass any one of the kwargs'''
        #if receiver is given, then below is executed
        engine_checker(cls)
        column = "receiver"
        col_secondary = "sender"
        query = user_receiver

        if not user_receiver:
            query = user_sender
            column = 'sender'
            col_secondary = "receiver"

        emails = []
        with cls.engine.connect() as conn:

            stmt = select(mails, users).where(mails.c[column]==query).join(users, mails.c[col_secondary]==users.c.id)
            result = conn.execute(stmt)
            if not user_sender:
                for row in result:               
                    emails.append(Email(row.text, (row.sender, row.username), row.receiver, id=row.id, date=row.date, time=row.time, read=row.read))
                return emails
            for row in result:
                emails.append(Email(row.text, row.sender, (row.receiver, row.username), id=row.id, date=row.date, time=row.time, read=row.read))
            return emails
        

    
    @classmethod
    def read(self, mail_id, user_id):
        engine_checker(self)
        stmt = update(mails).values(read=True).where(mails.c.id == mail_id, mails.c.receiver == user_id)
        with self.engine.begin() as conn:
            conn.execute(stmt)

    def __init__(self, message, sender, receiver, date=datetime.now().date(), time=datetime.now().time(), **data):
        self.message = message
        self.sender = sender
        self.receiver = receiver
        self.date = date
        self.time = time
        for key in data:
            self.key = data[key]

    def set(self):
        engine_checker(self)
        with self.engine.begin() as conn:
            stmt = insert(mails).values(text=self.message, sender=self.sender, receiver=self.receiver, date=self.date, time=self.time)            
            conn.execute(stmt)

            tmp = conn.execute(select(users.c.id, users.c.username).where(or_(users.c.id == self.receiver, users.c.id == self.sender))).fetchall()
            sender, receiver = (tmp[0][1], tmp[1][1]) if tmp[0][0] == self.sender else (tmp[1][1], tmp[0][1])
            logging.info(f"Email sent from {sender.title()} to {receiver.title()}")

def date(date):
    return date.strftime("%d %b")

if __name__ == "__main__":
    print("Metadata was called")
    metadata.create_all(engine)