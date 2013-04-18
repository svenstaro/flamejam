# -*- coding: utf-8 -*-

from flamejam import app, db
from datetime import datetime

RATING_CATEGORIES = ("gameplay", "graphics", "audio", "innovation", "story", "technical", "controls", "humor")

class Rating(db.Model):
    """The rating of a category is set to 0 to disable this category. It is
    then not counted into the average score.
    """

    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.SmallInteger)
    # score_CATEGORY = db.Column(db.SmallInteger, default = 5)
    text = db.Column(db.Text)
    posted = db.Column(db.DateTime)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, game, user, text, score):
        self.game = game
        self.user = user
        self.text = text
        self.posted = datetime.utcnow()
        self.score = score

    def __repr__(self):
        return '<Rating %r:%r>' % (self.id, self.score)

    def set(self, category, value):
        if category in (None, "overall"):
            self.score = value
        else:
            setattr(self, "score_" + category, value)

    def get(self, category):
        return self.score if category in (None, "overall") else getattr(self, "score_" + category)

# Add fields "dynamically"
for c in RATING_CATEGORIES:
    setattr(Rating, "score_" + c, db.Column(db.SmallInteger, default = 5))

