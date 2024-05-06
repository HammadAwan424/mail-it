from flask import session, redirect
from sqlalchemy import Table, Column, MetaData, Integer, String, \
    Boolean, ForeignKey, create_engine, insert, select, delete, update, exists, func, Date, Time, text
from datetime import datetime, timezone
import json
from functools import wraps
import logging
from typing import List, Dict
from markupsafe import escape


def logged_in(f):
    @wraps(f)
    def inner(*args,  **kwargs):
        user = session.get("user")
        if user is None:
            return redirect("/login")
        if not user.get("color"):
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
    Column("username", String, unique=True),
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
    Column("date", Date()),
    Column("time", Time()),   
    Column("read", Boolean, default=False)
)



class Email:
    _engine = None

    @property
    def engine(cls):
        if cls._engine == None:
            raise ValueError("Missing Engine")
        else:
            return cls._engine     

    @engine.setter
    def engine(cls, eng):
        cls._engine = eng


    # Pass any one of the below kwargs
    @classmethod
    def all_for(cls, receiver_id=None, sender_id=None, page=1, lmt=4, contains=''):
        if receiver_id is None and sender_id is None:
            raise TypeError("Need receiver or sender id")
        elif receiver_id is not None and sender_id is not None:
            raise TypeError("Can't have receiver and sender id simultaneously")

        # Give specified page based on the value of offset, lmt mails per page
        page = (page-1)*lmt

        # Query to return all mails with the same receiver else sender
        query = None
        c = mails.c.id.label("mail_id")
        if receiver_id:
            query = select(c, mails, users).where(mails.c.receiver==receiver_id).join(users, mails.c.sender==users.c.id) 
        if sender_id:
            query = select(c, mails, users).where(mails.c.sender==sender_id).join(users, mails.c.receiver==users.c.id)
        stmt = query.order_by(mails.c.date.desc(), mails.c.time.desc()).offset(page).limit(lmt).where(mails.c.text.contains(contains))
        

        mail_dicts = []
        with cls.engine.connect() as conn:
            column = (mails.c.receiver, receiver_id) if receiver_id else (mails.c.sender, sender_id)
            mail_count = conn.execute(select(func.count(mails.c.id)).where(column[0] == column[1])).scalar()
            

            for mapping in conn.execute(stmt).mappings().all():
                mail = dict(mapping)
                if receiver_id:
                    mail["sender"] = (mail['sender'], mail['username'], mail['color'])
                elif sender_id:
                    mail["receiver"] = (mail.receiver, mail.username, mail.color)
                mail_dicts.append(mail)
        return {"total": mail_count, "mails": mail_dicts, "count": len(mail_dicts), "perPage": lmt}
    

    @classmethod
    def all_for_receiver(cls, id=None, page=1, lmt=4, contains=''):

        # Offset so different pages can be returned
        offset = (page-1)*lmt

        # Query to return all mails with the same receiver
        c = mails.c.id.label("mail_id")
        query = select(c, mails, users).where(mails.c.receiver==id).join(users, mails.c.sender==users.c.id) 

        # Formats the query (Order, Descending, limit, searches for <contains>) 
        stmt = query.order_by(mails.c.date.desc(), mails.c.time.desc()).offset(offset).limit(lmt).where(mails.c.text.contains(contains))
        

        mail_dicts = []
        with cls.engine.connect() as conn:
            mail_count = conn.execute(select(func.count(mails.c.id)).where(mails.c.receiver == id)).scalar()

            for mapping in conn.execute(stmt).mappings().all():
                mail = dict(mapping)

                # Info about the sender of each mail
                mail["sender"] = (mail['sender'], mail['username'], mail['color'])
                mail_dicts.append(mail)
        return {"total": mail_count, "mails": mail_dicts, "count": len(mail_dicts), "perPage": lmt}
    

    @classmethod
    def all_for_sender(cls, id=None, page=1, lmt=4, contains=''):

        # Offset so different pages can be returned
        offset = (page-1)*lmt

        # Query to return all mails with the same sender
        c = mails.c.id.label("mail_id")
        query = select(c, mails, users).where(mails.c.sender==id).join(users, mails.c.receiver==users.c.id)

        # Formats the query (Order, Descending, limit, searches for <contains>)
        stmt = query.order_by(mails.c.date.desc(), mails.c.time.desc()).offset(offset).limit(lmt).where(mails.c.text.contains(contains))
        
        mail_dicts = []
        with cls.engine.connect() as conn:
            mail_count = conn.execute(select(func.count(mails.c.id)).where(mails.c.sender == id)).scalar()
            
            for mapping in conn.execute(stmt).mappings().all():
                mail = dict(mapping)

                # Info about the receiver of each mail  
                mail["receiver"] = (mail.receiver, mail.username, mail.color)
                mail_dicts.append(mail)
        return {"total": mail_count, "mails": mail_dicts, "count": len(mail_dicts), "perPage": lmt}        
    

    @classmethod
    def is_read(self, mail_id, receiver_id):
        stmt = update(mails).values(read=True).where(mails.c.id == mail_id, mails.c.receiver == receiver_id)
        with self.engine.begin() as conn:
            conn.execute(stmt)


    @classmethod
    def del_from_db(cls, mail_id, user_id):
        stmt = delete(mails).where(mails.c.id==mail_id, mails.c.receiver==user_id)
        with cls.engine.begin() as conn:
            conn.execute(stmt)


    def __init__(self, message, sender, receiver, date=None, time=None, **data):
        self.message = message
        self.sender = sender
        self.receiver = receiver
        self.date = date
        self.time = time
        if not date:
            current = datetime.now(timezone.utc)
            self.date = current.date()
        if not time:
            self.time = current.time()
        for key in data:
            setattr(self, key, data[key])


    def set(self, usrname: bool = False):
        # set usrname to True if username is stored on self.receiver, false if id
        rcvr = select(users.c.id).where(users.c.username == self.receiver).scalar_subquery() if usrname else self.receiver
        stmt = insert(mails).values(
            text=escape(self.message), sender=self.sender, receiver=rcvr, date=self.date, time=self.time
        )  
        
        with self.engine.begin() as conn:          
            conn.execute(stmt)

            # Logs info about the mail sent
            result = conn.execute(select(
                select(users.c.username).filter_by(id=self.sender).label("sender"), 
                select(users.c.username).filter_by(id=rcvr).label("receiver")
            )).fetchone()
            logging.info(f"Email sent from {result.sender.title()} to {result.receiver.title()}")


def myjson(python_mails):
    json_mails = json.dumps(python_mails, default=str, indent=2)
    return json_mails


if __name__ == "__main__":
    print("Metadata was called")
    metadata.create_all(engine)


class Schema:
    @classmethod
    def drop(self, engine):
        # engine.dispose()
        metadata.drop_all(engine)
    
    @classmethod
    def create(self, engine):
        metadata.create_all(engine)