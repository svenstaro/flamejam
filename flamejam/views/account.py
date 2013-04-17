from flamejam import app, db
from flamejam.login import *
from flamejam.models import User
from flamejam.forms import UserLogin, UserRegistration, ResetPassword, NewPassword, SettingsForm
from flask import render_template, redirect, flash, url_for
from smtplib import SMTPRecipientsRefused

@app.route('/login', methods=['GET', 'POST'])
def login():
    if get_current_user():
        flash("You are already logged in.", "info")
        return redirect(url_for("index"))

    next = request.args.get("next","")
    if next:
        # remember where we wanted to go
        session["next"] = next

    login_form = UserLogin()
    register_form = UserRegistration()

    if login_form.validate_on_submit():
        username = login_form.username.data
        password = hashPassword(login_form.password.data)
        user = User.query.filter_by(username=username).first()
        if not login_as(user):
            return redirect(url_for("verify_status", username=username))
        elif "next" in session:
            flash("You were logged in and redirected.", "success")
            return redirect(session.pop("next"))
        else:
            flash("You were logged in.", "success")
            return redirect(url_for('index'))
    elif register_form.validate_on_submit():
        username = register_form.username.data.strip()
        password = register_form.password.data
        email = register_form.email.data
        new_user = User(username,
                password,
                email,
                False, # no admin
                False  # is verified
                )

        m = Mail("Welcome to Bacon Game Jam, " + username)
        m.addRecipient(new_user)
        m.render("emails/account/verification.html", recipient = new_user)
        m.send()

        db.session.add(new_user)
        db.session.commit()

        flash("Your account has been created, confirm your email to verify.", "success")
        return redirect(url_for('verify_status', username = username))
    return render_template('account/login.html', login_form = login_form, register_form = register_form)

@app.route('/reset', methods=['GET', 'POST'])
def reset_request():
    if get_current_user():
        flash("You are already logged in.", "info")
        return redirect(url_for("index"))
    error = None
    form = ResetPassword()
    if form.validate_on_submit():
        # thanks to the UsernameValidator we cam assume the username exists
        user = User.query.filter_by(username=form.username.data).first()
        user.token = randint(0, sys.maxint)
        db.session.commit()

        m = Mail("Reset your BGJ-Password")
        m.addRecipient(user)
        m.render("emails/account/reset_password.html", recipient = user)
        m.send()

        flash("Your password has been reset, check your email.", "success")
    return render_template('reset_request.html', form=form, error=error)

@app.route('/reset/<username>/<token>', methods=['GET', 'POST'])
def reset_verify(username, token):
    user = user.query.filter_by(username=username).first_or_404()
    if user.token == None:
        flash("%s's account has not requested a password reset." % user.username.capitalize(), "error")
        return redirect(url_for('index'))
    if user.getResetToken() != token:
        flash("This does not seem to be a valid reset link, if you reset your account multiple times make sure you are using the link in the last email you received!", "error")
        return redirect(url_for('index'))
    form = NewPassword()
    error = None
    if form.validate_on_submit():
        # null the reset token
        user.token = None
        # set the new password
        user.password = hashPassword(form.password.data)
        db.session.commit()
        flash("Your password was updated and you can login with it now.", "success")
        return redirect(url_for('login'))
    return render_template('reset_newpassword.html', user = user, form = form, error = error)


@app.route('/verify/', methods=["POST", "GET"])
def verify_send():
    if request.method == 'GET':
        return redirect(url_for('index'))

    username = request.form.get('username', "")
    user = User.query.filter_by(username = username).first_or_404()

    if user.is_verified:
        flash("%s's account is already validated." % user.username.capitalize(), "info")
        return redirect(url_for('index'))


    m = Mail("Welcome to Bacon Game Jam, " + username)
    m.render("emails/account/verification.html", recipient = user)
    m.addRecipientEmail(user.new_email)
    m.send()

    flash("Verification has been resent, check your email", "success")
    return redirect(url_for('verify_status', username=username))

@app.route('/verify/<username>', methods=["GET"])
def verify_status(username):
    submitted = request.args.get('submitted', None)
    user = User.query.filter_by(username = username).first_or_404()

    if user.is_verified:
        flash("%s's account is already validated." % user.username.capitalize(), "info")
        return redirect(url_for('index'))

    return render_template('misc/verify_status.html', submitted=submitted, username=username)

@app.route('/verify/<username>/<verification>', methods=["GET"])
def verify(username, verification):

    user = User.query.filter_by(username = username).first_or_404()

    if user.is_verified:
        flash("%s's account is already validated." % user.username.capitalize(), "success")
        return redirect(url_for('index'))

    # verification success
    if verification == user.getVerificationHash():
        user.is_verified = True
        user.email = user.new_email
        db.session.commit()

        flash("Your email has been confirmed, you may now login")
        return redirect(url_for('login'))

    # verification failure
    else:
        return redirect(url_for('verify_status', username=username, submitted=True))

@app.route('/logout')
def logout():
    require_login()

    logout_now()
    flash("You were logged out.", "success")
    return redirect(url_for('index'))

@app.route('/profile')
def profile():
    require_login()
    return render_template("account/profile.html", user = get_current_user())

@app.route('/users/<username>/')
def show_user(username):
    user = User.query.filter_by(is_deleted = False, username = username).first_or_404()
    return render_template("account/profile.html", user = user)

@app.route('/settings', methods = ["POST", "GET"])
def settings():
    require_login()
    form = SettingsForm()
    user = get_current_user()
    logout = False

    if form.validate_on_submit():
        print "GO"
        user.ability_programmer = form.ability_programmer.data
        user.ability_gamedesigner = form.ability_gamedesigner.data
        user.ability_2dartist = form.ability_2dartist.data
        user.ability_3dartist = form.ability_3dartist.data
        user.ability_composer = form.ability_composer.data
        user.ability_sounddesigner = form.ability_sounddesigner.data
        user.abilities_extra = form.abilities_extra.data
        user.real_name = form.real_name.data
        user.about = form.about.data
        user.website = form.website.data
        user.pm_mode = form.pm_mode.data
        user.notify_new_jam = form.notify_new_jam.data
        user.notify_jam_start = form.notify_jam_start.data
        user.notify_jam_finish = form.notify_jam_finish.data
        user.notify_game_comment = form.notify_game_comment.data
        user.notify_team_changes = form.notify_team_changes.data
        user.notify_game_changes = form.notify_game_changes.data
        user.notify_team_invitation = form.notify_team_invitation.data
        user.notify_newsletter = form.notify_newsletter.data

        if user.location != form.location.data and form.location.data:
            new_loc, new_coords, new_flag = findLocation(form.location.data)
            if new_loc:
                user.location = form.location.data
                user.location_display = new_loc
                user.location_coords = new_coords
                user.location_flag = new_flag
                flash("Location was set to: " + new_loc, "success")
            else:
                flash("Could not find the location you entered.", "error")
        if not form.location.data:
            user.location = ""
            user.location_display = ""
            user.location_coords = ""
            user.location_flag = "unknown"

        if form.old_password.data and form.new_password.data and form.new_password2.data:
            if user.password != hashPassword(form.old_password.data):
                flash("Your password is incorrect. The password was not changed.", "error")
            else:
                user.password = hashPassword(form.new_password.data)
                flash("Your password was changed", "success")

        if user.email != form.email.data and form.email.data:
            user.new_email = form.email.data
            user.is_verified = False

            m = Mail("Please verify your new eMail address")
            m.addRecipientEmail(user.new_email)
            m.render("emails/account/verification.html", recipient = user, email_changed = True)
            m.send()

            logout = True
            flash("Your email address has changed. Please check your inbox for the verification.", "info")

        db.session.commit()
        flash("Your settings were saved.", "success")

        if logout:
            return redirect(url_for("logout"))
        else:
            return redirect(url_for("settings"))

    elif request.method == "GET":
        form.ability_programmer.data = user.ability_programmer
        form.ability_gamedesigner.data = user.ability_gamedesigner
        form.ability_2dartist.data = user.ability_2dartist
        form.ability_3dartist.data = user.ability_3dartist
        form.ability_composer.data = user.ability_composer
        form.ability_sounddesigner.data = user.ability_sounddesigner
        form.abilities_extra.data = user.abilities_extra
        form.real_name.data = user.real_name
        form.about.data = user.about
        form.website.data = user.website
        form.pm_mode.data = user.pm_mode
        form.location.data = user.location
        form.email.data = user.email
        form.notify_new_jam.data = user.notify_new_jam
        form.notify_jam_start.data = user.notify_jam_start
        form.notify_jam_finish.data = user.notify_jam_finish
        form.notify_game_comment.data = user.notify_game_comment
        form.notify_team_changes.data = user.notify_team_changes
        form.notify_game_changes.data = user.notify_game_changes
        form.notify_team_invitation.data = user.notify_team_invitation
        form.notify_newsletter.data = user.notify_newsletter

    return render_template('account/settings.html', form = form)

@app.errorhandler(404)
@app.errorhandler(403)
@app.errorhandler(500)
def error(error):
    return render_template("error.html", error = error), error.code

@app.errorhandler(SMTPRecipientsRefused)
def invalid_email(exception):
    flash("Invalid email address.", "error")
    return redirect(url_for('login'))

@app.errorhandler(flamejam.login.LoginRequired)
def login_required(exception):
    flash(exception.message, "error")
    return redirect(url_for('login', next = exception.next))

