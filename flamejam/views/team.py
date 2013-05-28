from flamejam import app, db
from flamejam.models import Jam, Team, Invitation, JamStatusCode, User
from flamejam.forms import TeamSettingsForm, InviteForm, LeaveTeamForm
from flask import render_template, url_for, redirect, flash, request
from flask.ext.login import login_required, current_user

@app.route('/jams/<jam_slug>/team/<int:team_id>/')
def jam_team(jam_slug, team_id):
    jam = Jam.query.filter_by(slug = jam_slug).first_or_404()
    team = Team.query.filter_by(id = team_id, jam_id = jam.id).first_or_404()
    return render_template('jam/team/info.html', jam = jam, team = team)

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
    jam = Jam.query.filter_by(slug = jam_slug).first_or_404()
    if jam.getStatus().code >= JamStatusCode.RATING:
        alert("The jam rating has started, so changes to the team are locked.", "error")
        return redirect(jam.url())

    r = current_user.getRegistration(jam)
    if not r or not r.team: abort(404)
    team = r.team

    settings_form = TeamSettingsForm(obj=team)
    invite_form = InviteForm()
    invite_username = None

    if settings_form.validate_on_submit():
        settings_form.populate_obj(team)
        team.livestreams.strip()
        db.session.commit()
        flash("The team settings were saved.", "success")
        return redirect(team.url())
    elif invite_form.validate_on_submit():
        invite_username = invite_form.username.data

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

            if i:
                flash("Invited user %s." % invite_username, "success")
            else:
                return redirect(url_for("invitation", id=i.id))

        return redirect(url_for("team_settings", jam_slug = team.jam.slug))

    return render_template('jam/team/edit.html', team = team, invite_form = invite_form, settings_form = settings_form)

@app.route('/invitations/')
@login_required
def invitations():
    return render_template("account/invitations.html", user = current_user)

@app.route('/invitations/<int:id>', methods = ["POST", "GET"])
@app.route('/invitations/<int:id>/<action>', methods = ["POST", "GET"])
@login_required
def invitation(id, action = ""):
    invitation = Invitation.query.filter_by(id = id).first_or_404()
    team = invitation.team

    if team.jam.getStatus().code >= JamStatusCode.RATING:
        flash("The jam rating has started, so changes to the team are locked.", "error")
        return redirect(team.url())

    if action == "accept":
        if current_user != invitation.user: abort(403)
        invitation.accept()
        flash("You have accepted the invitation.", "success")
        return redirect(team.url())
    elif action == "decline":
        if current_user != invitation.user: abort(403)
        invitation.decline()
        flash("You have declined the invitation.", "success")
        return redirect(team.url())
    elif action == "revoke":
        if current_user not in team.members: abort(403)
        db.session.delete(invitation)
        db.session.commit()
        flash("You have revoked the invitation for %s." % invitation.user.username, "success")
        return redirect(url_for("team_settings", jam_slug = team.jam.slug))
    else:
        if current_user != invitation.user and current_user not in team.members:
            abort(403)
        return render_template("jam/invitation.html", invitation=invitation)

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


