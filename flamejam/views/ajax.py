from flamejam import app

@app.route("/ajax/markdown", methods = ["POST"])
def ajax_markdown():
    return str(markdown_object(request.form["input"]))
