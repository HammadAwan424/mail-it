from flask import Flask, render_template, session, redirect, request
from flask_session import Session
from helpers import login as logn

app = Flask(__name__)

#Configure Session 
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = "./session"
app.config["SESSION_PERMANENT"] = False
Session(app)

@app.route("/")
@logn
def hello():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return "YOU CAME HERE BY GET"
    else:
        if session.get("id"):
            return redirect("/index")
        else:
            session["id"] = request.form.get("username")
            return redirect("/")