from flask import Flask, render_template, session, redirect, request
from flask_session import Session
from helpers import login, users, mails, Email, date
import logging
from sqlalchemy import insert, create_engine, exists, select, update


app = Flask(__name__)

app.jinja_env.filters["format"] = date

#Configure Session 
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = "./session"
app.config["SESSION_PERMANENT"] = False
Session(app)

logging.getLogger('werkzeug').disabled = True
logging.getLogger("sqlalchemy.engine.Engine").disabled = True
logging.basicConfig(
    level=logging.DEBUG, filename="logging.log",   
    format="%(message)s at %(asctime)s",
    datefmt="%X of %d %b",
)

engine = create_engine("sqlite:///database.db", echo=False)
Email.set_engine(engine)

@app.route("/")
@login
def index():
    with engine.connect() as conn:
        # check if profile is set up
        exists_color = conn.execute(select(users.c.color).where(users.c.id == session.get("id"))).scalar()
        if request.method == "GET" and not exists_color:
            return render_template("profile_color.html", session=session)
        
        #prepares page and returns it
        user = conn.execute(select(users).filter_by(id=session.get("id"))).first()
        mails = Email.all(user_receiver=session.get("id"))
        return render_template("index.html", mails=mails, user=user)

@app.route("/login", methods=["GET", "POST"])
def login():
    # manages for get request
    if request.method == "GET" and session.get("id") == None:
        return render_template("login.html")
    if request.method == "GET":
        session["id"] = None
        return redirect("/")
    

    user = request.form.get("username"), request.form.get("pass")
    with engine.connect() as conn:
        user = conn.execute(select(users).where(users.c.username == user[0], users.c.password == user[1])).first()
        if not user:
            return "We Couldn't Sign you in"
        
        session["username"] = user.username
        session["id"] = user.id
        logging.info(f"Logged In a User: {user[0]}")     
        return redirect("/user-profile")


@app.route("/user-profile", methods=["GET", "POST"])
def profile():
    if request.method == "GET" and not session.get("id"):
        return "You should come here like this"
    with engine.connect() as conn:
        exists_color = conn.execute(select(users.c.color).where(users.c.id == session.get("id"))).scalar()
        if request.method == "GET" and not exists_color:
            return render_template("profile_color.html", session=session)
    if request.method == "GET":
        return redirect("/")

    if request.method == "POST":
        with engine.begin() as conn:
            stmt = update(users).values(color = request.form.get("color")).where(users.c.id == session.get("id"))
            conn.execute(stmt)
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
    with engine.begin() as conn:
        result = conn.execute(stmt)
        session["id"] = result.lastrowid
        session["username"] = data[0]
        logging.info(f"Registered a User: {data[0]}")
        return redirect("/user-profile")