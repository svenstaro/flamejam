# -*- coding: utf-8 -*-

from flamejam import app, db
from flamejam.utils import get_slug
from flask import url_for
from datetime import datetime

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128))
    slug = db.Column(db.String(128))
    description = db.Column(db.Text)
    created = db.Column(db.DateTime)
    jam_id = db.Column(db.Integer, db.ForeignKey('jam.id'))
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    ratings = db.relationship('Rating', backref = 'game', lazy = "dynamic")
    comments = db.relationship('Comment', backref='game', lazy = "dynamic")
    packages = db.relationship('GamePackage', backref='game', lazy = "dynamic")
    screenshots = db.relationship('GameScreenshot', backref='game', lazy = "dynamic")

    def __init__(self, team, title):
        self.team = team
        self.jam = team.jam
        self.title = title
        self.slug = get_slug(title)
        self.created = datetime.utcnow()

    def __repr__(self):
        return '<Game %r>' % self.title

    def destroy(self):
        # destroy all ratings, comments, packages, screenshots
        for rating in self.ratings:
            db.session.delete(rating)
        for comment in self.comments:
            db.session.delete(comment)
        for package in self.packages:
            db.session.delete(package)
        for screenshot in self.screenshots:
            db.session.delete(screenshot)
        db.session.delete(self)

    def url(self, action = "", **values):
        return url_for("show_game", jam_slug = self.jam.slug, game_slug = self.slug, action = action, **values)

    def getAverageRating(self):
        categories = ["gameplay", "graphics","audio","innovation","story","technical", "controls", "overall"]
        r = {"average": 0}

        for c in categories:
            r[c] = 0

        ratings = len(self.ratings.all())
        if ratings > 0:
            for rating in self.ratings:
                for c in categories:
                    r[c] += getattr(rating, "score_" + c)
                r["average"] += rating.getAverage()

            for c in categories:
                r[c] *= 1.0 / ratings
            r["average"] *= 1.0 / ratings
        return r

    def getTotalScore(self):
        s = 0
        c = 0
        av = self.getAverageRating()
        for x in av:
            s += av[x]
            c += 1
        return s * 1.0/ c

    def getRank(self):
        jam_games = list(self.jam.games.all())
        jam_games.sort(cmp = gameCompare)
        return jam_games.index(self) + 1

    @staticmethod
    def compare(a, b):
        return a.getTotalScore() < b.getTotalScore()
