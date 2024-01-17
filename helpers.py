from flask import session, render_template
def login(f):
    def inner(*args,  **kwargs):
        if session.get("id") is None:
            return render_template("login.html")
        else:
            return f(*args,  **kwargs)
    return inner