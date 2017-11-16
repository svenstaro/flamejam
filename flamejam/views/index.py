from flamejam import app
from flamejam.utils import get_current_jam
from flamejam.models.jam import Jam
from flask import render_template, url_for, redirect


@app.route("/")
def index():
    jam = get_current_jam()
    return redirect(jam.url() if jam else url_for("home"))


@app.route("/home")
def home():
    return render_template("index.html", all_jams=Jam.query.all())
