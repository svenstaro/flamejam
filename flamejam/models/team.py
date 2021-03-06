from flamejam import app, db, mail
from flamejam.models.invitation import Invitation
from flask import url_for, render_template


class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jam_id = db.Column(db.Integer, db.ForeignKey("jam.id"))
    name = db.Column(db.String(80))

    description = db.Column(db.Text)
    livestreams = db.Column(db.Text)  # list of livestreams, one URL per file
    irc = db.Column(db.String(128))

    participations = db.relationship("Participation", backref="team", lazy="subquery")
    invitations = db.relationship("Invitation", backref="team", lazy="subquery")
    games = db.relationship("Game", backref="team", lazy="subquery")

    def __init__(self, user, jam):
        self.jam = jam
        self.user_join(user)
        self.name = user.username + "'s team"

    @property
    def members(self):
        return [r.user for r in self.participations]

    @property
    def game(self):
        return self.games[0] if self.games else None

    @property
    def is_single_team(self):
        return len(self.participations) == 1

    def url(self, **kwargs):
        return url_for("jam_team", jam_slug=self.jam.slug, team_id=self.id, **kwargs)

    def user_join(self, user):
        r = user.get_participation(self.jam)
        if not r:
            # register user, but do not create automatic team, we don't need
            # that anyway
            user.join_jam(self.jam, False)
        elif r in self.participations:
            return  # user is already in this team
        elif r.team and r.team != self:
            r.team.user_leave(user)

        r.team = self
        db.session.commit()

    def user_leave(self, user):
        r = user.get_participation(self.jam)

        if r.team != self:
            return  # not in this team, nevermind ;)

        if self.is_single_team:
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
    def number_members_and_invitations(self):
        return len(self.members) + len(self.invitations)

    def can_invite(self, user):
        return user in self.members and (
            self.jam.team_limit == 0 or self.jam.team_limit > self.number_members_and_invitations)

    def get_invitation(self, user):
        return Invitation.query.filter_by(user_id=user.id, team_id=self.id).first()

    def invite_user(self, user, sender):  # sender: which user sent the invitation
        if not user.notify_team_invitation:
            return None

        if self.get_invitation(user):
            i = self.get_invitation(user)  # already invited
        else:
            i = Invitation(self, user)
            db.session.add(i)
            db.session.commit()
            body = render_template("emails/invitation.txt", team=self, sender=sender,
                                   recipient=user, invitation=i)
            mail.send_message(
                subject=app.config["LONG_NAME"] + ": You have been invited to " + self.name,
                recipients=[user.email], body=body)
        return i
