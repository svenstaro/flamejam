# -*- coding: utf-8 -*-

from flamejam import app, db
from datetime import datetime

class DevlogPost(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"))
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    title = db.Column(db.String(128))
    content = db.Column(db.Text)
    posted = db.Column(db.DateTime)

    def __init__(self, team, author, title, content):
        self.team = team
        self.author = author
        self.title = title
        self.content = content
        self.posted = datetime.utcnow()

