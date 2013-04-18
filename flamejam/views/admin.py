from flamejam import app, db, admin_permission
from flamejam.utils import get_slug
from flamejam.models import User, Jam
from flamejam.forms import JamDetailsForm, AdminWriteAnnouncement
from flask import render_template, redirect, url_for, request, flash
from datetime import datetime

@app.route("/admin")
def admin_index():
    return redirect(url_for('admin_users'))

@app.route("/admin/users")
@admin_permission.require()
def admin_users():
    users = User.query.all()
    return render_template("admin/users.html", users = users)

@app.route("/admin/users/form", methods = ["POST"])
@admin_permission.require()
def admin_users_form():
    users = []
    for field in request.form:
        print field
        if field[:5] == "user-" and request.form[field] == "on":
            i = field[5:]
            users.append(User.query.filter_by(id = i).first_or_404())

    for user in users:
        if request.form["submit"] == "Toggle Deleted":
            user.is_deleted = not user.is_deleted
        if request.form["submit"] == "Toggle Admin":
            user.is_admin = not user.is_admin

    db.session.commit()

    flash(str(len(users)) + " users were changed", "success")

    return redirect(url_for("admin_users"))

@app.route("/admin/users/<username>")
@app.route("/admin/user/<username>")
@admin_permission.require()
def admin_user(username):
    user = User.query.filter_by(username = username).first_or_404()
    return render_template("admin/user.html", user = user)

@app.route("/admin/jams")
@admin_permission.require()
def admin_jams():
    return render_template("admin/jams.html", jams = Jam.query.all())

@app.route("/admin/jams/<int:id>", methods = ["POST", "GET"])
@app.route("/admin/jams/create/", methods = ["POST", "GET"])
@admin_permission.require()
def admin_jam(id = 0):
    mode = "create"
    jam = None

    if id != 0:
        jam = Jam.query.filter_by(id = id).first_or_404()
        mode = "edit"

    form = JamDetailsForm(obj=jam)

    if form.validate_on_submit():
        slug_jam = Jam.query.filter_by(slug = get_slug(form.title.data.strip())).first()
        if slug_jam and slug_jam != jam:
            flash("A jam with a similar title already exists (slug conflict).", "error")
        else:
            if mode == "create":
                jam = Jam("", datetime.utcnow())
                db.session.add(jam)

            form.populate_obj(jam)
            jam.title.strip()
            jam.slug = get_slug(jam.title)
            jam.theme.strip()
            jam.description.strip()
            jam.restrictions.strip()

            db.session.commit()
            flash("Jam settings have been saved.", "success")
            return redirect(url_for("admin_jam", id = jam.id))

    return render_template("admin/jam.html", id = id, mode = mode, jam = jam, form = form)

@app.route("/admin/announcement", methods = ["GET", "POST"])
@admin_permission.require()
def admin_announcement():
    form = AdminWriteAnnouncement()

    if form.validate_on_submit():
        for user in User.filter_by(notify_useletter = True).all():
            body = render_template("emails/newsletter.txt", recipient=new_user, message=form.message.data)
            mail.send_message(subject="BaconGameJam Newsletter: " + form.subject.data, recipients=[user.email], body=body)
        flash("Your announcement has been sent to the users.")

    return render_template("admin/announcement.html", form = form)
