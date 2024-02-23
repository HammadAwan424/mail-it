from flask import Flask, render_template, session, redirect, request
from flask_session import Session
from helpers import users, mails, Email, myjson, logged_in
import logging
from sqlalchemy import insert, create_engine, exists, select, update
import json


app = Flask(__name__)



app.jinja_env.filters["myjson"] = myjson

#Configure Session 
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = "./session"
app.config["SESSION_PERMANENT"] = False
Session(app)

#Configure Logging
logging.getLogger('werkzeug').disabled = True
logging.getLogger("sqlalchemy.engine.Engine").disabled = True
logging.basicConfig(
    level=logging.DEBUG, filename="logging.log",   
    format="%(message)s at %(asctime)s",
    datefmt="%X of %d %b",
)

engine = create_engine("sqlite:///database.db", echo=False)
Email.engine = engine

@app.route("/")
@logged_in
def index():
    mails = Email.all_for(receiver_id=session.get('user').get("id"))
    return render_template("index.html", mails=mails)

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
    
    stmt = insert(users).values(username=data[0], password=data[1])
    with engine.begin() as conn:
        result = conn.execute(stmt)
        session["user"] = {"id": result.lastrowid ,"username": data[0]}
        logging.info(f"Registered a User: {data[0]}")
        return redirect("/user-profile")
    

@app.route("/read")
@logged_in
def read():
    mail = request.args.get("mail_id")
    Email.is_read(mail_id=mail, user_id=session["user"]["id"])
    return myjson({"status": "success", "message": f"Email {mail} marked as read"})

@app.route("/send")
@logged_in
def send():
    mails = Email.all_for(receiver_id=session.get("user").get("id"))
    return myjson({"mails": mails})