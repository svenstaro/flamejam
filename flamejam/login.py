from flamejam import *
from flamejam.models import Participant
from flask import has_request_context, session, abort, request

class LoginRequired(Exception):
    def __init__(self, message = "You need to be logged in to view this page.", next = ""):
        self.message = message
        self.next = next

current_user = None

def get_current_user():
    global current_user
    return current_user

@app.before_request
def check_login():
    global current_user
    current_user = None
    if "login_id" in session:
        user_id = session["login_id"]
        print("User " + str(user_id) + " requested")
        current_user = Participant.query.filter_by(id = user_id).first()

def login_as(user):
    session["login_id"] = user.id

def logout_now():
    session.pop("login_id")

def require_login(message = "You need to be logged in to view this page."):
    if not current_user:
        raise LoginRequired(message, request.url)

def require_user(user):
    require_login()
    if (isinstance(user, list) and not current_user in user) or user != current_user:
        abort(403)

def require_admin():
    require_login()
    if not current_user.is_admin:
        abort(403)
