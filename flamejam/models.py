from datetime import datetime, timedelta
from hashlib import sha512
from flamejam import db, filters
from flask import url_for

class Participant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(128))
    email = db.Column(db.String(256), unique=True)
    is_admin = db.Column(db.Boolean)
    is_verified = db.Column(db.Boolean)
    registered = db.Column(db.DateTime)
    entries = db.relationship('Entry', backref='participant', lazy='dynamic')
    ratings = db.relationship('Rating', backref='participant', lazy='dynamic')
    comments = db.relationship('Comment', backref='participant', lazy='dynamic')

    def __init__(self, username, password, email, is_admin=False,
            is_verified=False):
        self.username = username
        self.password = sha512(password).hexdigest()
        self.email = email
        self.is_admin = is_admin
        self.is_verified = is_verified
        self.registered = datetime.utcnow()

    def __repr__(self):
        return '<User %r>' % self.username

class JamStatusCode(object):
    ANNOUNCED   = 0
    RUNNING     = 1
    PACKAGING   = 2
    VOTING      = 3
    FINISHED    = 4

class JamStatus(object):
    def __init__(self, code, time):
        self.code = code
        self.time = time

    def __repr__(self):
        t = filters.formattime(self.time)
        d = filters.humandelta(datetime.utcnow(), self.time)
        if self.code == JamStatusCode.ANNOUNCED:
            return "Announced for {0}".format(t)
        elif self.code == JamStatusCode.RUNNING:
            return "Running until {0} ({1} left)".format(t, d)
        elif self.code == JamStatusCode.PACKAGING:
            return "Packaging until {0} ({1} left)".format(t, d)
        elif self.code == JamStatusCode.VOTING:
            return "Voting until {0} ({1} left)".format(t, d)
        elif self.code == JamStatusCode.PACKAGING:
            return "Finished since {0}".format(t)

class Jam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    short_name = db.Column(db.String(16), unique=True)
    long_name = db.Column(db.String(128), unique=True)
    theme = db.Column(db.String(128))
    announced = db.Column(db.DateTime) # Date on which the jam was announced
    start_time = db.Column(db.DateTime) # The jam starts at this moment
    end_time = db.Column(db.DateTime) # The jamming phase ends at this moment
    packaging_deadline = db.Column(db.DateTime) # Packaging ends at this moment
    rating_end = db.Column(db.DateTime) # Rating period ends and jam is over
    entries = db.relationship('Entry', backref='jam', lazy='dynamic')

    def __init__(self, short_name, long_name, start_time, end_time=None,
            packaging_deadline=None, voting_end=None, theme = ''):
        self.short_name = short_name
        self.long_name = long_name
        self.start_time = start_time
        self.theme = theme

        if end_time is None:
            self.end_time = start_time + timedelta(days=2)
        else:
            self.end_time = end_time

        if packaging_deadline is None:
            self.packaging_deadline = start_time + timedelta(days=3)
        else:
            self.packaging_deadline = packaging_deadline

        if self.rating_end is None:
            self.rating_end = start_time + timedelta(days=7)
        else:
            self.rating_end = rating_end

        self.announced = datetime.utcnow()

    def __repr__(self):
        return '<Jam %r>' % self.short_name

    def getStatus(self):
        now = datetime.utcnow()
        if self.start_time > now:
            return JamStatus(JamStatusCode.ANNOUNCED, self.start_time)
        elif self.end_time > now:
            return JamStatus(JamStatusCode.RUNNING, self.end_time)
        elif self.packaging_deadline > now:
            return JamStatus(JamStatusCode.PACKAGING, self.packaging_deadline)
        elif self.voting_end > now:
            return JamStatus(JamStatusCode.VOTING, self.voting_end)
        else:
            return JamStatus(JamStatusCode.FINISHED, self.end_time)
            
    def getFullName(self):
        return "{0} [{1}]".format(self.long_name, self.short_name)
    
    def url(self):
        return url_for('show_jam', jam_name = self.short_name) 

class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    description = db.Column(db.Text)
    posted = db.Column(db.DateTime)
    jam_id = db.Column(db.Integer, db.ForeignKey('jam.id'))
    participant_id = db.Column(db.Integer, db.ForeignKey('participant.id'))
    ratings = db.relationship('Rating', backref='entry', lazy='dynamic')
    comments = db.relationship('Comment', backref='entry', lazy='dynamic')

    def __init__(self, name, description, jam, participant):
        self.name = name
        self.description = description
        self.jam = jam
        self.participant = participant
        self.posted = datetime.utcnow()

    def __repr__(self):
        return '<Entry %r>' % self.name

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    score_graphics = db.Column(db.SmallInteger)
    score_audio = db.Column(db.SmallInteger)
    score_innovation = db.Column(db.SmallInteger)
    score_humor = db.Column(db.SmallInteger)
    score_fun = db.Column(db.SmallInteger)
    score_overall = db.Column(db.SmallInteger)
    text = db.Column(db.Text)
    posted = db.Column(db.DateTime)
    entry_id = db.Column(db.Integer, db.ForeignKey('entry.id'))
    participant_id = db.Column(db.Integer, db.ForeignKey('participant.id'))

    def __init__(self, score_graphics, score_audio, score_innovation,
        score_humor, score_fun, score_overall, text, entry, participant):
        self.score_graphics = score_graphics
        self.score_audio = score_audio
        self.score_innovation = score_innovation
        self.score_humor = score_humor
        self.score_fun = score_fun
        self.score_overall = score_overall
        self.text = text
        self.entry = entry
        self.participant = participant
        self.posted = datetime.utcnow()

    def __repr__(self):
        return '<Rating %r>' % self.id

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text)
    posted = db.Column(db.DateTime)
    entry_id = db.Column(db.Integer, db.ForeignKey('entry.id'))
    participant_id = db.Column(db.Integer, db.ForeignKey('participant.id'))

    def __init__(self, text, entry, participant):
        self.text = text
        self.entry = entry
        self.participant = participant
        self.posted = datetime.utcnow()

    def __repr__(self):
        return '<Comment %r>' % self.id


class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    text = db.Column(db.Text)
    posted = db.Column(db.DateTime)

    def __init__(self, text):
        self.text = text
        self.posted = datetime.utcnow()

    def __repr__(self):
        return '<Announcement %r>' % self.id
