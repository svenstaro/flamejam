# -*- coding: utf-8 -*-

from flamejam import app, db, mail
from flamejam.models import Invitation, Game
from flask import url_for, render_template

class Team(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    jam_id = db.Column(db.Integer, db.ForeignKey("jam.id"))
    name = db.Column(db.String(80))

    description = db.Column(db.Text)
    livestreams = db.Column(db.Text) # list of livestreams, one URL per file
    irc = db.Column(db.String(128))

    registrations = db.relationship("Registration", backref = "team", lazy = "subquery")
    invitations = db.relationship("Invitation", backref = "team", lazy = "subquery")
    games = db.relationship("Game", backref = "team", lazy = "subquery")

    def __init__(self, user, jam):
        self.jam = jam
        self.userJoin(user)
        self.name = user.username + "'s team"

    @property
    def members(self):
        return [r.user for r in self.registrations]

    @property
    def game(self):
        return self.games[0] if Game.query.filter_by(is_deleted=False).count() else None

    @property
    def isSingleTeam(self):
        return len(self.registrations) == 1

    def url(self, **values):
        return url_for("jam_team", jam_slug = self.jam.slug, team_id = self.id, **values)

    def userJoin(self, user):
        r = user.getRegistration(self.jam)
        if not r:
            # register user, but do not create automatic team, we don't need
            # that anyway
            user.joinJam(self.jam, False)
        elif r in self.registrations:
            return # user is already in this team
        elif r.team and r.team != self:
            r.team.userLeave(user)

        r.team = self
        db.session.commit()

    def userLeave(self, user):
        r = user.getRegistration(self.jam)

        if r.team != self:
            return # not in this team, nevermind ;)

        if self.isSingleTeam:
            # only user in team, we can destroy this team
            self.destroy()

        r.team = None
        db.session.commit()

    def destroy(self):
        # also destroy all the games, invitations
        for game in self.games:
            game.destroy()
        for invitation in self.invitations:
            db.session.delete(invitation)
        db.session.delete(self)

    @property
    def numberMembersAndInvitations(self):
        return len(self.members) + self.invitations.count()

    def canInvite(self, user):
        return user in self.members and (self.jam.team_limit == 0 or self.jam.team_limit > self.numberMembersAndInvitations)

    def getInvitation(self, user):
        return Invitation.query.filter_by(user_id = user.id, team_id = self.id).first()

    def inviteUser(self, user, sender): # sender: which user sent the invitation
        if not user.notify_team_invitation:
            return None

        if self.getInvitation(user):
            i = self.getInvitation(user) # already invited
        else:
            i = Invitation(self, user)
            db.session.add(i)
            db.session.commit()
            body = render_template("emails/invitation.txt", team=self, sender=sender, recipient=user, invitation=i)
            mail.send_message(subject=app.config["LONG_NAME"] +": You have been invited to " + self.name, recipients=[user.email], body=body)
        return i

