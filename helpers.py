from flask import session, redirect
from sqlalchemy import Table, Column, MetaData, Integer, String, Boolean, ForeignKey, create_engine, insert

def login(f):
    def inner(*args,  **kwargs):
        if session.get("id") is None:
            return redirect("/login")
        else:
            return f(*args,  **kwargs)
    return inner


engine = create_engine("sqlite:///database.db", echo=True)
metadata = MetaData()

users = Table(
    "users", 
    metadata,
    Column("id", Integer, primary_key=True),
    Column("username", String(30)), #uniqute constraint
    Column("password", String)
)

mails = Table(
    "mails",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("text", String),
    Column("sender", ForeignKey("users.id"), nullable=False),
    Column("receiver", ForeignKey("users.id"), nullable=False),
    Column("date", String), #dates in alchemy    
    Column("read", Boolean, default=False)
)

def engine_chekcer(obj):
    if obj.engine == None:
        raise ValueError("Missing Engine")
    else:
        return obj.engine

class Email:

    engine = None

    @classmethod
    def set_engine(cls, engine):
        cls.engine = engine

    def __init__(self, message, sender, receiver):
        self.message = message
        self.sender = sender
        self.receiver = receiver

    def set(self):
        engine = engine_chekcer(self)
        with engine.begin() as conn:
            stmt = insert(mails).values(text=self.text, sender=self.sender, receiver=self.receiver)
            conn.execute(stmt)

    def read(self):
        ...

    def get(self):
        ...


if __name__ == "__main__":
    print("Metadata was called")
    metadata.create_all(engine)