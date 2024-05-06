# This code is for development and includes certain shortcuts for basic tasks for testing purposes
from sqlalchemy import users, select, engine
from flask import redirect, session
from helpers import Email



from __main__ import app

@app.route("/check")
def check():
    stmt = select(users.c.username).where(users.c.username.startswith("hammad"))
    print(stmt)
    return "he"

@app.route("/hello")
def hello():
    return redirect("/world")
    return "hello world"

@app.route("/world")
def world():
    # lst = None
    # with engine.connect() as conn:
    #     lst = conn.execute(select(users.c.username)).fetchall()
    # return str(lst)
    return "hello world"
    allusers = users.query.all()
    return str(allusers)
    return render_template('login.html')
    return "world"

    
@app.route("/union")
def union():
    # first = select(("sender " + users.c.username).label("s")).where(users.c.id == 1)
    # second = select(("receiver " + users.c.username).label("r")).where(users.c.id == 2)
    # q = first.union(second)
    # print(q)
    with engine.connect() as conn:

        # result = conn.execute(text(
        #     "SELECT (SELECT users.username FROM users WHERE users.id = :sid) as sender, \
        #         (SELECT users.username FROM users WHERE users.id = :rid) as receiver"
        #     ), {"sid": 2, "rid": 1}).fetchone()
        # first = select(users.c.username.label("ds")).filter_by(id=1).cte()
        # second = select(users.c.username).filter_by(id=2).cte()

        # first = select(users.c.username).filter_by(id=1).label("sender")
        # second = select(users.c.username).filter_by(id=2).label("receiver")
        # result = conn.execute(select(
        #     select(users.c.username).filter_by(id=1).label("sender"), 
        #     select(users.c.username).filter_by(id=2).label("receiver")
        # )).fetchone()
        rcvr = select(users.c.id).where(users.c.username == "hammad").scalar_subquery()
        stmt = select(users).where(users.c.id == rcvr)
        result = conn.execute(stmt)
        print(result.fetchone())
        print(stmt)
    return "successful"


@app.route("/set/<name>/<message>")
def set(name, message):
    # return str(session.get("user").get("id"))
    mail = Email(message, session.get("user").get("id"), name)
    mail.set(usrname=True)
    return "successful"


@app.route("/test/sub")
def fsdf():
    stmt = select(users.c.username.label("hello"), users.c.username).where(users.c.username=='hammad')
    print(stmt)
    result = None
    with engine.connect() as conn:
        result = conn.execute(stmt).mappings().all()
    return str(result)