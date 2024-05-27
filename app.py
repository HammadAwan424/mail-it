from flask import Flask, render_template, session, redirect, request, abort, jsonify
from flask_session import Session
from helpers import users, mails, Email, myjson, logged_in, Config, MailForm, apology
import logging
from sqlalchemy import insert, create_engine, exists, select, update, Column, Integer, String, Table
import json
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import timedelta
from markupsafe import escape
from datetime import timedelta

app = Flask(__name__)

if os.environ.get("ENV") == "ProductionMailit":
    Config.LoadProductionConfig(app.config)
else:
    Config.LoadDevelopmentConfig(app.config)

db = SQLAlchemy(app)

app.jinja_env.filters["myjson"] = myjson

# Configure Session 
app.config['SESSION_SQLALCHEMY'] = db
Session(app)

# Initialize Self created Class, Email in helpers.py
engine = create_engine(Config.get("DATABASE_URL"))
Email.engine = engine

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
        current_user = conn.execute(select(users).where(users.c.username == data[0], users.c.password == data[1])).first()
        
        if not current_user:
            return "You haven't registered"
        
        session["user"] = {"id": current_user.id, "username": current_user.username, 'color': current_user.color}
        logging.info(f"Logged In a User: {current_user[0]}")  
        return redirect("/")


@app.route("/user-profile", methods=["GET", "POST"])
def profile():
    # if user not signed in
    if session.get("user") is None:
        logging.info("redirecting to login cuz not logged in from color")
        return redirect("/login")
    
    # preprocessing for GET request
    id = session.get("user").get("id")
    with engine.connect() as conn:
        exists_color = conn.execute(select(users.c.color).where(users.c.id == id)).scalar()

        # GET request
        if request.method == "GET" and exists_color:
            return redirect("/")
        
        if request.method == "GET" and not exists_color:
            return render_template("profile_color.html")
    
    # POST request
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
    data = escape(request.form.get("name")), request.form.get("pass"), request.form.get("con_pass")
    print(data)
    if not data[0] or not data[1]:
        return "Please don't leave a field empty"
    if data[1] != data[2]:
        return "Please provide same password"
    if len(data[1]) < 8:
        return "Atleast 8 characters are required"
    
    stmt = insert(users).values(username=data[0], password=data[1]).returning(users.c.id)
    with engine.begin() as conn:
        result = conn.execute(stmt).fetchone()
        session["user"] = {"id": result.id ,"username": str(data[0])}
        logging.info(f"Registered a User: {data[0]}")
        return redirect("/user-profile")
    

@app.route("/read")
@logged_in
def read():
    mail = request.args.get("mail_id")
    Email.is_read(mail_id=mail, receiver_id=session.get("user")["id"])
    return myjson({"status": "success", "message": f"Email {mail} marked as read"})


@app.route("/send", methods=["GET", "POST"])
@logged_in
def send():
    mailform = MailForm(engine, data=request.json, sender=session.get("user").get("id"))

    if not mailform.validate():
        FirstInvalidatedFieldErrors = next(iter(mailform.errors.values()))
        body = {
            "error": FirstInvalidatedFieldErrors[0] # First error of FirstInvalidatedField
        }
        logging.debug(f"{body}")
        logging.debug(f"{mailform.errors}")
        return apology(body, 400)

    mail = Email(**mailform.data)
    mail.set(usrname=True)
    return jsonify({"status": "success"})


@app.route("/api/page/<int:page>")
@logged_in
def api(page):
    mails = Email.all_for(receiver_id=session["user"]["id"], page=page)
    if not len(mails['mails']):
        return abort(404)
    template =  render_template("components.html", serverSideMails=mails['mails'], page_request=True)
    response = myjson({"mails": mails, "template": template})
    return response

@app.route("/autocomplete/<mode>/<path:query>")
@logged_in
def autocomplete(mode, query):
    modes = ["username", "mails"]
    if mode not in modes:
        return abort(404)
    
    query = escape(query)
    id = session.get('user').get("id")
    
    if mode == "username":
        user_name = select(users.c.username).where(users.c.id == id).scalar_subquery()

        stmt = select(users.c.username.regexp_replace(query, f'<strong>{query}</strong>').label("username")).where(
            users.c.username.startswith(query), users.c.username != user_name
        ).limit(3)

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
    Email.del_from_db(mail_id=body.get('mail_id'), user_id=session.get('user')['id'])
    return "successful"
