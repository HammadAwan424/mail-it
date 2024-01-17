from flask import Flask, render_template
from flask_session import Session

app = Flask(__name__)

#Configure Session 
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_CACHE_DIR"] = "/session"
app.config["SESSION_PERMANENT"] = False
Session(app)

@app.route("/")
def hello():
    return render_template("index.html")
