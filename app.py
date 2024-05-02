from flask import Flask, render_template, session, redirect, request, abort
from flask_session import Session
from helpers import users, mails, Email, myjson, logged_in, Schema
import logging
from sqlalchemy import insert, create_engine, exists, select, update, Column, Integer, String, Table
import json
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import timedelta
from markupsafe import escape
from config import CONFIG
from datetime import timedelta

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = CONFIG['DATABASE_URL']
db = SQLAlchemy(app)

app.jinja_env.filters["myjson"] = myjson

# Configure Session 
app.config["SESSION_TYPE"] = "sqlalchemy"
app.config["SESSION_PERMANENT"] = False
app.config['SESSION_SQLALCHEMY'] = db
app.config['SQLALCHEMY_ECHO'] = True
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)

Session(app)

# Initialize Self created Class, Email in helpers.py
engine = create_engine(CONFIG['DATABASE_URL'])
Email.engine = engine


# Initialize OR Drop Tables for testing
# with app.app_context():
#     Schema.create(engine)
# with app.app_context():
#     Schema.drop(engine)


# Configure Logging
logging.getLogger('werkzeug').disabled = True
logging.getLogger("sqlalchemy.engine.Engine").disabled = True
logging.basicConfig(
    level=logging.DEBUG,   
    format="%(message)s at %(asctime)s",
    datefmt="%X of %d %b",
)


@app.route("/")
@logged_in
def index():
    mails = Email.all_for(receiver_id=session.get('user').get("id"))
    return render_template("index.html", mails=mails, serverSideJson=myjson(mails))


@app.route("/login", methods=["GET", "POST"])
def login():
    # manages for get request
    if request.method == "GET" and session.get("user") == None:
        return render_template("login.html")
    if request.method == "GET":
        session["user"] = None
        return redirect("/")
    
    # manages post request
    data = request.form.get("username"), request.form.get("pass")
    with engine.connect() as conn:
        db_user = conn.execute(select(users).where(users.c.username == data[0], users.c.password == data[1])).first()
        if not db_user:
            return "You haven't registered"
        
        session["user"] = {"id": db_user.id, "username": db_user.username}
        logging.info(f"Logged In a User: {db_user[0]}")  
        logging.info("redirecting to user profile from login, set up")   
        return redirect("/user-profile")


@app.route("/user-profile", methods=["GET", "POST"])
def profile():
    # if user not signed in
    if session.get("user") is None:
        logging.info("redirecting to login cuz not logged in from color")
        return redirect("/login")
    
    # preprocessing for get request
    id = session.get("user").get("id")
    with engine.connect() as conn:
        exists_color = conn.execute(select(users.c.color).where(users.c.id == id)).scalar()

        if request.method == "GET" and exists_color:
            session["user"]["color"] = exists_color
            logging.info("to homepage everythin set up from color")
            return redirect("/")
        
        if request.method == "GET":
            return render_template("profile_color.html")
        
    if request.method == "POST":
        with engine.begin() as conn:
            stmt = update(users).values(color = request.form.get("color")).where(users.c.id == id)
            conn.execute(stmt)
            session["user"]["color"] = request.form.get("color")
            logging.info("to home page after set up from color")
            return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET" and session.get("user"):
        return redirect("/")
    if request.method == "GET":
        return render_template("register.html")
        
    
    #manages post request    
    data = request.form.get("name"), request.form.get("pass"), request.form.get("con_pass")
    if not data[0] or not data[1]:
        return "Please don't leave a field empty"
    if data[1] != data[2]:
        return "Please provide same password"
    if len(data[1]) < 8:
        return "Atleast 8 characters are required"
    
    stmt = insert(users).values(username=data[0], password=data[1]).returning(users.c.id)
    with engine.begin() as conn:
        result = conn.execute(stmt).fetchone()
        session["user"] = {"id": result.id ,"username": data[0]}
        logging.info(f"Registered a User: {data[0]}")
        return redirect("/user-profile")
    

@app.route("/read")
@logged_in
def read():
    mail = request.args.get("mail_id")
    Email.is_read(mail_id=mail, user_id=session["user"]["id"])
    return myjson({"status": "success", "message": f"Email {mail} marked as read"})

@app.route("/send", methods=["GET", "POST"])
@logged_in
def send():
    data = {
        "sender": session["user"]["id"],
        "receiver": request.json.get("receiver"),
        "subject": request.json.get("subject"),
        "message": request.json.get("message")
    }
    mail = Email(data["message"], data["sender"], data["receiver"])
    mail.set(usrname=True)
    return "success"


@app.route("/api/page/<int:page>")
@logged_in
def api(page):
    mails = Email.all_for(receiver_id=session["user"]["id"], page=page)
    if not len(mails['mails']):
        return abort(404)
    template =  render_template("components.html", serverSideMails=mails['mails'], page_request=True)
    response = myjson({"mails": mails, "template": template})
    return response

@app.route("/autocomplete/<mode>/<query>")
@logged_in
def autocomplete(mode, query):
    modes = ["username", "mails"]
    if mode not in modes:
        return abort(404)

    id = session.get('user').get("id")
    if mode == "username":
        user_name = select(users.c.username).where(users.c.id == id).scalar_subquery()

        stmt = select(users.c.username.regexp_replace(query, f'<strong>{query}</strong>').label("username")).where(
            users.c.username.startswith(query), users.c.username != user_name
        ).limit(3)
        print(query)

        conn = engine.connect()
        result = conn.execute(stmt).mappings().all()
        conn.close()
        return render_template("components.html", serverSideUsers=result, user_search_request=True)
        
    if mode == "mails":
        result = Email.all_for(receiver_id=id, lmt=3, contains=query)['mails']
        return render_template("components.html", serverSideMails=result, mail_search_request=True)


@app.route("/delete", methods=["POST"])
@logged_in
def delete():
    body = request.json
    Email.del_from_db(mail_id=body.get('mail_id'), user=session.get('user'))
    return "successful"
