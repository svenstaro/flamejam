from flamejam import app, db, admin_permission, mail
from flamejam.utils import get_slug
from flamejam.models import User, Jam, Game
from flamejam.forms import JamDetailsForm, AdminWriteAnnouncement, AdminUserForm
from flask import render_template, redirect, url_for, request, flash
from flask.ext.mail import Message
from datetime import datetime
from smtplib import SMTPRecipientsRefused

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
        if field[:5] == "user-" and request.form[field] == "on":
            i = field[5:]
            users.append(User.query.filter_by(id = i).first_or_404())

    for user in users:
        if request.form["submit"] == "Toggle Deleted":
            user.is_deleted = not user.is_deleted
        if request.form["submit"] == "Toggle Admin":
            user.is_admin = not user.is_admin
        if request.form["submit"] == "Toggle Verified":
            user.is_verified = not user.is_verified
            if user.is_verified and user.new_email:
                user.email = user.new_email

    db.session.commit()

    flash(str(len(users)) + " users were changed", "success")

    return redirect(url_for("admin_users"))

@app.route("/admin/games/form", methods = ["POST"])
@admin_permission.require()
def admin_games_form():
    games = []
    for field in request.form:
        if field[:5] == "game-" and request.form[field] == "on":
            i = field[5:]
            games.append(Game.query.filter_by(id = i).first_or_404())

    for game in games:
        if request.form["submit"] == "Toggle Deleted":
            game.is_deleted = not game.is_deleted
        if request.form["submit"] == "Toggle Cheated":
            game.has_cheated = not game.has_cheated

    db.session.commit()

    flash(str(len(games)) + " games were changed", "success")

    return redirect(url_for("admin_games"))

@app.route("/admin/user/<username>", methods = ["POST", "GET"])
@admin_permission.require()
def admin_user(username):
    user = User.query.filter_by(username = username).first_or_404()
    form = AdminUserForm(obj=user)

    if form.validate_on_submit():
        other = User.query.filter_by(username = form.username.data).first()
        if other and other.id != user.id:
            flash("A user with that username already exists. Please choose another.", "error")
        else:
            user.username = form.username.data
            user.avatar = form.avatar.data
            user.email = form.email.data
            db.session.commit()
            flash("User changed successfully.", "success")
            return redirect(url_for("admin_user", username = user.username))

    return render_template("admin/user.html", user = user, form = form)

@app.route("/admin/jams")
@admin_permission.require()
def admin_jams():
    return render_template("admin/jams.html", jams = Jam.query.all())

@app.route("/admin/jams/<int:id>/send/<int:n>", methods = ["POST", "GET"])
@admin_permission.require()
def admin_jam_notification(id, n):
    jam = Jam.query.filter_by(id = id).first_or_404()
    jam.sendNotification(n)
    flash("Notification sent.", "success")
    return redirect(url_for("admin_jam", id = id))

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

@app.route("/admin/games")
@admin_permission.require()
def admin_games():
    return render_template("admin/games.html", jams = Jam.query.all())

@app.route("/admin/games/<int:id>/<flag>")
@admin_permission.require()
def admin_game_flag(id, flag):
    game = Game.query.filter_by(id=id).first_or_404()
    if flag == "deleted":
        flash("Toggled deleted flag")
        game.is_deleted = not game.is_deleted
        db.session.commit()
    if flag == "cheated":
        flash("Toggled cheated flag")
        game.has_cheated = not game.has_cheated
        db.session.commit()
    return redirect(url_for('admin_games'))

@app.route("/admin/announcement", methods = ["GET", "POST"])
@admin_permission.require()
def admin_announcement():
    form = AdminWriteAnnouncement()

    if form.validate_on_submit():
        with mail.connect() as conn:
            for user in User.query.filter_by(notify_newsletter = True).all():
                body = render_template("emails/newsletter.txt", recipient=user, message=form.message.data)
                subject = app.config["LONG_NAME"] + " Newsletter: " + form.subject.data
                sender = app.config['MAIL_DEFAULT_SENDER']
                recipients = [user.email]
                message = Message(subject=subject, sender=sender, body=body, recipients=recipients)
                try:
                    conn.send(message)
                except SMTPRecipientsRefused:
                    pass
        flash("Your announcement has been sent to the users.")

    return render_template("admin/announcement.html", form = form)

@app.route("/admin/users/delete/<username>")
@admin_permission.require()
def admin_user_delete(username):
    u = User.query.filter_by(username = username).first()
    if not u: return "User not found"

    for r in u.participations:
        u.leaveJam(r.jam)
    for i in u.invitations:
        db.session.delete(i)
    db.session.delete(u)
    db.session.commit()

    return "User " + username + " deleted"
