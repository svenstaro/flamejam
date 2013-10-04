# -*- coding: utf-8 -*-

from flamejam import app, db
from flamejam.utils import get_slug, average, average_non_zero
from flamejam.models.gamescreenshot import GameScreenshot
from flamejam.models.rating import Rating, RATING_CATEGORIES
from flask import url_for
from datetime import datetime

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128))
    slug = db.Column(db.String(128))
    created = db.Column(db.DateTime)
    description = db.Column(db.Text)
    technology = db.Column(db.Text)
    help = db.Column(db.Text)
    is_deleted = db.Column(db.Boolean, default = False)
    has_cheated = db.Column(db.Boolean, default = False)

    jam_id = db.Column(db.Integer, db.ForeignKey('jam.id'))
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    ratings = db.relationship('Rating', backref = 'game', lazy = "subquery")
    comments = db.relationship('Comment', backref='game', lazy = "subquery")
    packages = db.relationship('GamePackage', backref='game', lazy = "subquery")
    screenshots = db.relationship('GameScreenshot', backref='game', lazy = "subquery")

    # score_CATEGORY_enabled = db.Column(db.Boolean, default = True)

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

    def url(self, **values):
        return url_for("show_game", jam_slug = self.jam.slug, game_id = self.id, **values)

    @property
    def screenshotsOrdered(self):
        return sorted(self.screenshots, lambda s1, s2: int(s1.index - s2.index))

    @property
    def score(self):
        if self.has_cheated:
            return -10

        return average([r.score for r in self.ratings if not r.user.is_deleted]) or 0

    def feedbackAverage(self, category):
        if category in (None, "overall"):
            return self.score
        return average_non_zero([r.get(category) for r in self.ratings])

    @property
    def rank(self):
        jam_games = list(self.jam.games.all())
        jam_games.sort(key="score", reverse=True)
        return jam_games.index(self) + 1

    @property
    def numberRatings(self):
        return len(self.ratings)

    @property
    def ratingCategories(self):
        return [c for c in RATING_CATEGORIES if getattr(self, "score_" + c + "_enabled")]

    def getRatingByUser(self, user):
        return Rating.query.filter_by(user_id=user.id).first()

# Adds fields "dynamically" (which score categories are enabled?)
for c in RATING_CATEGORIES:
    setattr(Game, "score_" + c + "_enabled", db.Column(db.Boolean, default = True))
