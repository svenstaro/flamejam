from flamejam import app, db, mail
from flamejam.models import User
from flamejam.utils import hashPassword
from flamejam.forms import UserLogin, UserRegistration, ResetPassword, NewPassword, SettingsForm, ContactUserForm
from flask import render_template, redirect, flash, url_for, current_app, session, request, abort
from smtplib import SMTPRecipientsRefused
from flask.ext.login import login_required, login_user, logout_user, current_user
from flask.ext.principal import AnonymousIdentity, Identity, UserNeed, identity_changed, identity_loaded, Permission, RoleNeed, PermissionDenied

@app.route('/login', methods=['GET', 'POST'])
def login():
    login_form = UserLogin()
    register_form = UserRegistration()

    if login_form.validate_on_submit():
        username = login_form.username.data
        password = hashPassword(login_form.password.data)
        remember_me = login_form.remember_me.data
        user = User.query.filter_by(username=username).first()
        if login_user(user, remember_me):
            flash("You were logged in.", "success")
            return redirect(request.args.get("next") or url_for('index'))

            # Tell Flask-Principal the identity changed
            identity_changed.send(current_app._get_current_object(),
                                  identity=Identity(user.id))
        else:
            flash("Login failed, user not validated", "error")
            return redirect(url_for("verify_status", username=username))

    elif register_form.validate_on_submit():
        username = register_form.username.data.strip()
        password = register_form.password.data
        email = register_form.email.data

        new_user = User(username, password, email)

        body = render_template("emails/account/verification.txt", recipient = new_user, email_changed = False)
        mail.send_message(subject="Welcome to " + app.config["LONG_NAME"] + ", " + username, recipients=[new_user.email], body=body)

        db.session.add(new_user)
        db.session.commit()

        flash("Your account has been created, confirm your email to verify.", "success")
        return redirect(url_for('verify_status', username = username))
    return render_template('account/login.html', login_form = login_form, register_form = register_form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You were logged out.", "success")

    # Remove session keys set by Flask-Principal
    for key in ('identity.name', 'identity.auth_type'):
        session.pop(key, None)

    # Tell Flask-Principal the user is anonymous
    identity_changed.send(current_app._get_current_object(),
                          identity=AnonymousIdentity())

    return redirect(url_for('index'))

# we need this so Flask Principal knows what to do when a user is loaded
@identity_loaded.connect_via(app)
def on_identity_loaded(sender, identity):
    # Set the identity user object
    identity.user = current_user

    # Add the UserNeed to the identity
    if hasattr(current_user, 'id'):
        identity.provides.add(UserNeed(current_user.id))

    if hasattr(current_user, 'is_admin'):
        if current_user.is_admin:
            identity.provides.add(RoleNeed('admin'))

@app.route('/reset', methods=['GET', 'POST'])
def reset_request():
    if current_user:
        flash("You are already logged in.", "info")
        return redirect(url_for("index"))
    error = None
    form = ResetPassword()
    if form.validate_on_submit():
        # thanks to the UsernameValidator we cam assume the username exists
        user = User.query.filter_by(username=form.username.data).first()
        user.token = randint(0, sys.maxint)
        db.session.commit()

        body = render_template("emails/account/reset_password.txt", recipient=user)
        mail.send_message(subject=app.config["LONG_NAME"] + ": Reset your password", recipients=[user.email], body=body)

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

    body=render_template("emails/account/verification.txt", recipient=user)
    mail.send_message(subject="Welcome to " + app.config["LONG_NAME"] + ", " + username, recipients=[user.new_email], body=body)

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

@app.route('/profile')
@login_required
def profile():
    return render_template("account/profile.html", user = current_user)

@app.route('/users/<username>/')
def show_user(username):
    user = User.query.filter_by(is_deleted = False, username = username).first_or_404()
    return render_template("account/profile.html", user = user)

@app.route('/users/<username>/contact/', methods = ("POST", "GET"))
@login_required
def contact_user(username):
    user = User.query.filter_by(is_deleted = False, username = username).first_or_404()
    if user == current_user or user.pm_mode == "disabled":
        abort(403)

    form = ContactUserForm()

    if form.validate_on_submit():
        message = form.message.data
        body = render_template("emails/account/message.txt", recipient=user, sender=current_user, message=message)
        mail.send_message(subject=app.config["LONG_NAME"] + ": New message from " + current_user.username,
            recipients=[user.email], reply_to=current_user.email, body=body)

    return render_template("account/contact.html", user = user, form = form)

@app.route('/settings', methods = ["POST", "GET"])
@login_required
def settings():
    user = current_user
    form = SettingsForm(obj=user)
    logout = False

    if form.validate_on_submit():
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

            body = render_template("emails/account/verification.txt", recipient=user, email_changed = True)
            mail.send_message(subject=app.config["LONG_NAME"] + ": eMail verification", recipients=[user.email], body=body)

            logout = True
            flash("Your email address has changed. Please check your inbox for the verification.", "info")

        db.session.commit()
        flash("Your settings were saved.", "success")

        if logout:
            return redirect(url_for("logout"))
        else:
            return redirect(url_for("settings"))

    return render_template('account/settings.html', form = form)

#@app.errorhandler(500)
@app.errorhandler(404)
@app.errorhandler(403)
@app.errorhandler(PermissionDenied)
def error(error):
    code = error.code if hasattr(error, "code") else 403
    return render_template("error.html", error = error, code = code), code or 403

@app.errorhandler(SMTPRecipientsRefused)
def invalid_email(exception):
    flash("Invalid email address.", "error")
    return redirect(url_for('login'))
