# -*- coding: utf-8 -*-

from flamejam import app, db
from flamejam.models.jam import JamStatusCode
from flask import url_for

class Invitation(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    def __init__(self, team, user):
        self.team = team
        self.user = user

    def url(self, **values):
        return url_for("invitation", id = self.id, _external = True, **values)

    def canAccept(self):
        return self.team.jam.getStatus().code <= JamStatusCode.PACKAGING

    def accept(self):
        self.team.userJoin(self.user)
        db.session.delete(self)
        db.session.commit()

    def decline(self):
        db.session.delete(self)
        db.session.commit()

