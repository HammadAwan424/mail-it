from flask import Flask, render_template, session, redirect, request
from flask_session import Session
from helpers import login, users, mails, Email
import logging
from sqlalchemy import insert, create_engine, exists, select


app = Flask(__name__)

#Configure Session 
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = "./session"
app.config["SESSION_PERMANENT"] = False
Session(app)

werkzeug_log = logging.getLogger('werkzeug')
werkzeug_log.disabled = True
logging.basicConfig(level=logging.DEBUG, filename="logging.log")

engine = create_engine("sqlite:///database.db")

@app.route("/")
@login
def hello():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    # manages for get request
    if request.method == "GET" and session.get("id") == None:
        return render_template("login.html")
    elif request.method == "GET":
        return render_template("index.html")
    
    #manages for post request
    else:
        user = request.form.get("username"), request.form.get("pass")
        with engine.connect() as conn:
            result = conn.execute(select(users).where(users.c.username == user[0], users.c.password == user[1]))
            if result.scalar():
                logging.info(f"Logged In a User: {user[0]}")
                return "Worked Like A Charm"
        return "Coundn't sign in"
        session["id"] = request.form.get("username")
        return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    
    #manages post request    
    data = request.form.get("name"), request.form.get("pass"), request.form.get("con_pass")

    if data[1] != data[2]:
        return "Please provide same password"
    if len(data[1]) < 8:
        return "Atleast 8 characters are required"
    
    stmt = insert(users).values(username=data[0], password=data[1])
    engine = create_engine("sqlite:///database.db", echo=True)
    with engine.begin() as conn:
        result = conn.execute(stmt)
        session["id"] = result.lastrowid
        logging.info(f"Registered a User: {data[0]}")
        return redirect("/")
