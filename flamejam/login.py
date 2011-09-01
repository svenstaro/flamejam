from flamejam import *
from flamejam.models import Participant
from flask import has_request_context, session, abort, request, flash
from httplib import HTTPConnection, HTTPResponse
import json

class LoginRequired(Exception):
    def __init__(self, message = "You need to be logged in to view this page.", next = ""):
        self.message = message
        self.next = next

def get_current_user():
    if "login_user" in session:
        return session["login_user"]
        # return Participant.query.filter_by(id = session["login_id"]).first()
    return None

@app.before_request
def check_login():
    # refresh the user object in the session
    if "login_id" in session:
        session["login_user"] = Participant.query.filter_by(id = session["login_id"]).first()
        if not get_current_user():
            logout_now()

def login_as(user):
    if not user.is_verified:
        flash("Your account is not verified.")
        return False
    session["login_id"] = user.id
    session["login_user"] = user
    return True

def logout_now():
    if "login_id" in session:
        session.pop("login_id")
    if "login_user" in session:
        session.pop("login_user")

def require_login(message = "You need to be logged in to view this page."):
    if not get_current_user():
        raise LoginRequired(message, request.url)

def require_user(user):
    require_login()
    islist = isinstance(user, list)
    if (islist and not get_current_user() in user) or (not islist and user != get_current_user()):
        abort(403)

def require_admin():
    require_login()
    if not get_current_user().is_admin:
        abort(403)

# Commented out because we removed reddit verification
"""def check_reddit(username, hash):
    connection = HTTPConnection(app.config['REDDIT_SERVER'])
    url = app.config['REDDIT_CONFIRM_THREAD'] + ".json"
    data = ""
    while True:
        connection.request("GET", url)
        response = connection.getresponse()
        if response.status == 200:
            data = response.read()
            break
        elif response.status == 302:
            url = response.getheader("location")
            connection.close()
        else:
            flash("Error fetching verification thread.")
            return False

    if data:
        # check every response.node.data.children with kind="t1" for
        # data.author and data.body
        # see the reddit API

        things = json.loads(data)
        for thing in things:
            if not "data" in thing:
                continue
            if not "children" in thing["data"]:
                continue

            for child in thing["data"]["children"]:
                if not "kind" in child:
                    continue
                if child["kind"] == "t1": # is a comment
                    data = child["data"]
                    print("FOUND COMMENT BY " + data["author"]+ ": " + data["body"])
                    if data["author"] == username and hash in data["body"]:
                        return True

    return False"""
