from flamejam import app, markdown_object
from flask import request

@app.route("/ajax/markdown", methods = ["POST"])
def ajax_markdown():
    return str(markdown_object(request.form["input"]))
