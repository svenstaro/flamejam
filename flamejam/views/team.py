from flamejam import app, db
from flamejam.models import Jam, Team, DevlogPost, Invitation
from flamejam.login import *
from flamejam.forms import DevlogForm, TeamSettingsForm, InviteForm
from flask import render_template, url_for, redirect, flash

@app.route('/jams/<jam_slug>/team/<int:team_id>/')
def jam_team(jam_slug, team_id):
    jam = Jam.query.filter_by(slug = jam_slug).first_or_404()
    team = Team.query.filter_by(id = team_id, jam_id = jam.id).first_or_404()
    return render_template('jam/team.html', jam = jam, team = team)

@app.route('/jams/<jam_slug>/team/devlog/', methods = ["POST", "GET"])
@app.route('/jams/<jam_slug>/team/devlog/<int:edit_id>', methods = ["POST", "GET"])
def jam_devlog(jam_slug, edit_id = 0):
    require_login()
    jam = Jam.query.filter_by(slug = jam_slug).first_or_404()
    r = get_current_user().getRegistration(jam)
    if not r or not r.team: abort(403)

    form = DevlogForm()
    mode = "create"

    if edit_id:
        p = DevlogPost.query.filter_by(id = edit_id).first_or_404()
        if p.team != r.team: abort(403)
        mode = "edit"

    if form.validate_on_submit():
        if mode == "edit":
            p.title = form.title.data
            p.content = form.text.data
        else:
            p = DevlogPost(r.team, get_current_user(), form.title.data, form.text.data)
            db.session.add(p)
        db.session.commit()
        flash("Your post was successfully saved.", "success")
        return redirect(r.team.url())
    elif mode == "edit" and request.method == "GET":
        form.title.data = p.title
        form.text.data = p.content

    return render_template('jam/write_devlog.html', jam = jam, team = r.team, form = form, mode = mode, edit_id = edit_id)


@app.route('/jams/<jam_slug>/team/')
def jam_current_team(jam_slug):
    require_login()
    jam = Jam.query.filter_by(slug = jam_slug).first_or_404()
    user = get_current_user()
    r = user.getRegistration(jam)
    if r:
        return redirect(r.team.url())
    else:
        return redirect(jam.url())

@app.route('/jams/<jam_slug>/team/settings', methods = ["POST", "GET"])
def team_settings(jam_slug):
    require_login()

    settings_form = TeamSettingsForm()
    invite_form = InviteForm()
    invite_username = None

    jam = Jam.query.filter_by(slug = jam_slug).first_or_404()
    r = get_current_user().getRegistration(jam)
    if not r or not r.team: abort(404)
    team = r.team

    if settings_form.validate_on_submit():
        team.name = settings_form.name.data
        team.wip = settings_form.wip.data
        team.livestreams = settings_form.livestreams.data.strip()
        team.irc = settings_form.irc.data
        db.session.commit()
        flash("The team settings were saved.", "success")
        return redirect(team.url())
    elif invite_form.validate_on_submit():
        invite_username = invite_form.username.data
    elif request.method == "GET":
        settings_form.name.data = team.name
        settings_form.wip.data = team.wip
        settings_form.livestreams.data = team.livestreams
        settings_form.irc.data = team.irc

    if "invite" in request.args:
        invite_username = request.args["invite"]

    if invite_username:
        user = User.query.filter_by(username = invite_username, is_deleted = False).first()
        if not user:
            flash("Could not find user: %s" % invite_username, "error")
        elif user.inTeam(team):
            flash("User %s is already in this team." % invite_username, "warning")
        elif team.getInvitation(user):
            flash("User %s is already invited." % user.username, "warning")
        else:
            i = team.inviteUser(user, get_current_user())
            flash("Invited user %s." % invite_username, "success")

        return redirect(team.url())

    return render_template('jam/team_settings.html', team = team, invite_form = invite_form, settings_form = settings_form)

@app.route('/invitations/<int:id>', methods = ["POST", "GET"])
@app.route('/invitations/<int:id>/<action>', methods = ["POST", "GET"])
def invitation(id, action = ""):
    invitation = Invitation.query.filter_by(id = id).first_or_404()
    require_user(invitation.user)

    if action == "accept":
        invitation.accept()
        flash("You have accepted the invitation.", "success")
        return redirect(invitation.team.url())
    elif action == "decline":
        invitation.decline()
        flash("You have declined the invitation.", "success")
        return redirect(invitation.team.url())
    else:
        return render_template("jam/invitation.html", invitation = invitation)

