from flamejam import app, db
from flamejam.models import Jam, Team, DevlogPost, Invitation, JamStatusCode
from flamejam.forms import DevlogForm, TeamSettingsForm, InviteForm, LeaveTeamForm
from flask import render_template, url_for, redirect, flash
from flask.ext.login import login_required, current_user

@app.route('/jams/<jam_slug>/team/<int:team_id>/')
def jam_team(jam_slug, team_id):
    jam = Jam.query.filter_by(slug = jam_slug).first_or_404()
    team = Team.query.filter_by(id = team_id, jam_id = jam.id).first_or_404()
    return render_template('jam/team/info.html', jam = jam, team = team)

@app.route('/jams/<jam_slug>/team/devlog/', methods = ["POST", "GET"])
@app.route('/jams/<jam_slug>/team/devlog/<int:edit_id>', methods = ["POST", "GET"])
@login_required
def jam_devlog(jam_slug, edit_id = 0):
    jam = Jam.query.filter_by(slug = jam_slug).first_or_404()
    r = current_user.getRegistration(jam)
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
            p = DevlogPost(r.team, current_user, form.title.data, form.text.data)
            db.session.add(p)
        db.session.commit()
        flash("Your post was successfully saved.", "success")
        return redirect(r.team.url())
    elif mode == "edit" and request.method == "GET":
        form.title.data = p.title
        form.text.data = p.content

    return render_template('jam/team/devlog.html', jam = jam, team = r.team, form = form, mode = mode, edit_id = edit_id)


@app.route('/jams/<jam_slug>/team/')
@login_required
def jam_current_team(jam_slug):
    jam = Jam.query.filter_by(slug = jam_slug).first_or_404()
    user = current_user
    r = user.getRegistration(jam)
    if r:
        return redirect(r.team.url())
    else:
        return redirect(jam.url())

@app.route('/jams/<jam_slug>/team/settings', methods = ["POST", "GET"])
@login_required
def team_settings(jam_slug):
    settings_form = TeamSettingsForm()
    invite_form = InviteForm()
    invite_username = None

    jam = Jam.query.filter_by(slug = jam_slug).first_or_404()
    if jam.getStatus().code >= JamStatusCode.RATING:
        alert("The jam rating has started, so changes to the team are locked.", "error")
        return redirect(jam.url())

    r = current_user.getRegistration(jam)
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
        if not team.canInvite(current_user):
            flash("You cannot invite someone right now.", "error")
            abort(403)

        user = User.query.filter_by(username = invite_username, is_deleted = False).first()
        if not user:
            flash("Could not find user: %s" % invite_username, "error")
        elif user.inTeam(team):
            flash("User %s is already in this team." % invite_username, "warning")
        elif team.getInvitation(user):
            flash("User %s is already invited." % user.username, "warning")
        else:
            i = team.inviteUser(user, current_user)
            flash("Invited user %s." % invite_username, "success")

        return redirect(url_for("team_settings", jam_slug = team.jam.slug))

    return render_template('jam/team/edit.html', team = team, invite_form = invite_form, settings_form = settings_form)

@app.route('/invitations/<int:id>', methods = ["POST", "GET"])
@app.route('/invitations/<int:id>/<action>', methods = ["POST", "GET"])
def invitation(id, action = ""):
    invitation = Invitation.query.filter_by(id = id).first_or_404()

    if invitation.team.jam.getStatus().code >= JamStatusCode.RATING:
        alert("The jam rating has started, so changes to the team are locked.", "error")
        return redirect(invitation.team.url())

    if action == "accept":
        require_user(invitation.user)
        invitation.accept()
        flash("You have accepted the invitation.", "success")
        return redirect(invitation.team.url())
    elif action == "decline":
        require_user(invitation.user)
        invitation.decline()
        flash("You have declined the invitation.", "success")
        return redirect(invitation.team.url())
    elif action == "revoke":
        require_user(invitation.team.members)
        db.session.delete(invitation)
        db.session.commit()
        flash("You have revoked the invitation for %s." % invitation.user.username, "success")
        return redirect(url_for("team_settings", jam_slug = invitation.team.jam.slug))
    else:
        require_user(invitation.user)
        return render_template("jam/invitation.html", invitation = invitation)

@app.route("/jams/<jam_slug>/leave-team/", methods = ("POST", "GET"))
@login_required
def leave_team(jam_slug):
    jam = Jam.query.filter_by(slug = jam_slug).first_or_404()

    if jam.getStatus().code >= JamStatusCode.RATING:
        alert("The jam rating has started, so changes to the team are locked.", "error")
        return redirect(jam.url())

    user = current_user
    r = user.getRegistration(jam)

    if not r or not r.team:
        flash("You are in no team.", "info")
        return redirect(jam.url())

    if jam.getStatus().code > JamStatusCode.PACKAGING:
        flash("You cannot change the team after packaging is finished.", "error")
        return redirect(jam.url())

    team = r.team
    form = LeaveTeamForm()

    if form.validate_on_submit():
        team.userLeave(user)
        user.generateTeam(jam)
        db.session.commit()
        flash("You are now unregistered from this jam.", "success")
        return redirect(jam.url())

    return render_template("jam/team/leave.html", jam = jam, form = form, team = team)


