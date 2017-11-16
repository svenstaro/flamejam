from flamejam import db
from datetime import datetime


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text)
    posted = db.Column(db.DateTime)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, text, game, user):
        self.text = text
        self.game = game
        self.user = user
        self.posted = datetime.utcnow()

    def __repr__(self):
        return f'<Comment {self.id}>'
