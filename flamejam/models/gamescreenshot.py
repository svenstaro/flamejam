# -*- coding: utf-8 -*-

from flamejam import app, db

class GameScreenshot(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    url = db.Column(db.String(255))
    caption = db.Column(db.Text)
    index = db.Column(db.Integer) # 0..n-1
    game_id = db.Column(db.Integer, db.ForeignKey("game.id"))

    def __init__(self, url, caption, game):
        self.game = game
        self.url = url
        self.caption = caption
        self.index = len(self.game.screenshots) - 1

    def __repr__(self):
        return "<GameScreenshot %r>" % self.id

    def move(self, x):
        all = self.game.screenshotsOrdered

        old = self.index
        new = self.index + x

        if new >= len(all):
            new = len(all) - 1
        if new < 0:
            new = 0

        if new != self.index:
            other = all[new]
            self.index = new
            other.index = old
