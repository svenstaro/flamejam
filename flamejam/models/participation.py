# -*- coding: utf-8 -*-

from flamejam import app, db
from datetime import datetime

class Participation(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"))
    jam_id = db.Column(db.Integer, db.ForeignKey("jam.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    show_in_finder = db.Column(db.Boolean, default = True)
    registered = db.Column(db.DateTime)

    def __init__(self, user, jam, show_in_finder = True):
        self.user = user
        self.jam = jam
        self.show_in_finder = show_in_finder
        self.registered = datetime.utcnow()

