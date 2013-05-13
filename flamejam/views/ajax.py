from flamejam import app, markdown_object
from flamejam.models import User
from flask import request, render_template

@app.route("/ajax/markdown", methods = ["POST"])
def ajax_markdown():
    return str(markdown_object(request.form["input"]))

@app.route("/ajax/map-user/<username>/")
def ajax_mapuser(username):
    user = User.query.filter_by(username = username).first()
    return render_template("ajax/mapuser.html", user = user)
