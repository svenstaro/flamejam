# -*- coding: utf-8 -*-

from flamejam import app, db
from datetime import datetime

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    score_gameplay = db.Column(db.SmallInteger)
    score_graphics = db.Column(db.SmallInteger)
    score_audio = db.Column(db.SmallInteger)
    score_innovation = db.Column(db.SmallInteger)
    score_story = db.Column(db.SmallInteger)
    score_technical = db.Column(db.SmallInteger)
    score_controls = db.Column(db.SmallInteger)
    score_overall = db.Column(db.SmallInteger)
    text = db.Column(db.Text)
    posted = db.Column(db.DateTime)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, score_gameplay, score_graphics, score_audio, score_innovation,
        score_story, score_technical, score_controls, score_overall, text, game, user):
        self.score_gameplay = score_gameplay
        self.score_graphics = score_graphics
        self.score_audio = score_audio
        self.score_innovation = score_innovation
        self.score_story = score_story
        self.score_technical = score_technical
        self.score_controls = score_controls
        self.score_overall = score_overall
        self.text = text
        self.game = game
        self.user = user
        self.posted = datetime.utcnow()

    def __repr__(self):
        return '<Rating %r>' % self.id

    def getAverage(self):
        return (self.score_gameplay
            + self.score_graphics
            + self.score_audio
            + self.score_innovation
            + self.score_story
            + self.score_technical
            + self.score_controls
            + self.score_overall) * 1.0 / 8.0


