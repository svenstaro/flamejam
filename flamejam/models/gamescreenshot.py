# -*- coding: utf-8 -*-

from flamejam import app, db

class GameScreenshot(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    url = db.Column(db.String(256))
    caption = db.Column(db.Text)
    game_id = db.Column(db.Integer, db.ForeignKey("game.id"))

    def __init__(self, url, caption, game):
        self.game = game
        self.url = url
        self.caption = caption

    def __repr__(self):
        return "<GameScreenshot %r>" % self.id

