# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from hashlib import sha512, md5
from flamejam import db, filters
from flask import url_for, Markup
import re

def get_slug(s):
    s = s.lower()
    s = re.sub(r"[\s_+]+", "-", s)
    s = re.sub("[^a-z0-9\-]", "", s)
    return s


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
    jams = db.relationship('Jam', backref='author', lazy='dynamic')

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

    def url(self):
        return url_for('show_participant', username = self.username)

    def getAvatar(self, size = 32):
        return "http://www.gravatar.com/avatar/{0}?s={1}&d=identicon".format(md5(self.email.lower()).hexdigest(), size)

    def getLink(self):
        s = 12
        return Markup('<a class="user" href="{0}"><img width="{2}" height="{2}" src="{3}" class="icon"/> {1}</a>'.format(
            self.url(), self.username, s, self.getAvatar(s)))


class JamStatusCode(object):
    ANNOUNCED   = 0
    RUNNING     = 1
    PACKAGING   = 2
    RATING      = 3
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
        elif self.code == JamStatusCode.RATING:
            return "Rating until {0} ({1} left)".format(t, d)
        elif self.code == JamStatusCode.PACKAGING:
            return "Finished since {0}".format(t)

class Jam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(128), unique=True)
    title = db.Column(db.String(128), unique=True)
    theme = db.Column(db.String(128))
    announced = db.Column(db.DateTime) # Date on which the jam was announced
    start_time = db.Column(db.DateTime) # The jam starts at this moment
    end_time = db.Column(db.DateTime) # The jamming phase ends at this moment
    packaging_deadline = db.Column(db.DateTime) # Packaging ends at this moment
    rating_end = db.Column(db.DateTime) # Rating period ends and jam is over
    entries = db.relationship('Entry', backref='jam', lazy='dynamic')
    author_id = db.Column(db.Integer, db.ForeignKey('participant.id'))

    def __init__(self, title, author, start_time, end_time=None,
            packaging_deadline=None, voting_end=None, theme = ''):
        self.title = title
        self.slug = get_slug(title)
        self.start_time = start_time
        self.theme = theme
        self.author = author

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
        return '<Jam %r>' % self.slug

    def getStatus(self):
        now = datetime.utcnow()
        if self.start_time > now:
            return JamStatus(JamStatusCode.ANNOUNCED, self.start_time)
        elif self.end_time > now:
            return JamStatus(JamStatusCode.RUNNING, self.end_time)
        elif self.packaging_deadline > now:
            return JamStatus(JamStatusCode.PACKAGING, self.packaging_deadline)
        elif self.rating_end > now:
            return JamStatus(JamStatusCode.RATING, self.rating_end)
        else:
            return JamStatus(JamStatusCode.FINISHED, self.end_time)

    def url(self):
        return url_for('show_jam', jam_slug = self.slug)

class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128))
    slug = db.Column(db.String(128))
    description = db.Column(db.Text)
    posted = db.Column(db.DateTime)
    jam_id = db.Column(db.Integer, db.ForeignKey('jam.id'))
    participant_id = db.Column(db.Integer, db.ForeignKey('participant.id'))
    ratings = db.relationship('Rating', backref='entry', lazy='dynamic')
    comments = db.relationship('Comment', backref='entry', lazy='dynamic')
    packages = db.relationship('EntryPackage', backref='entry', lazy='dynamic')
    screenshots = db.relationship('EntryScreenshot', backref='entry', lazy='dynamic')

    def __init__(self, title, description, jam, participant):
        self.title = title
        self.slug = get_slug(title)
        self.description = description
        self.jam = jam
        self.participant = participant
        self.posted = datetime.utcnow()

    def __repr__(self):
        return '<Entry %r>' % self.name

    def url(self, action = ""):
        return url_for("show_entry", jam_slug = self.jam.slug, entry_slug = self.slug, action = action)

def entry_package_type_string(type):
    if type == "web":       return "Web link (Flash etc.)"
    if type == "linux":       return "Binaries: Linux general"
    if type == "linux32":       return "Binaries: Linux 32-bit"
    if type == "linux64":       return "Binaries: Linux 64-bit"
    if type == "windows":       return "Binaries: Windows general"
    if type == "windows32":       return "Binaries: Windows 32-bit"
    if type == "windows64":       return "Binaries: Windows 64-bit"
    if type == "mac":       return "Binaries: MacOS Application"
    if type == "source":       return "Source: package"
    if type == "git":       return "Source: Git repository"
    if type == "svn":       return "Source: SVN repository"
    if type == "hg":       return "Source: HG repository"
    if type == "combi":       return "Combined package: Linux + Windows + Source (+ more, optional)"
    if type == "love":       return "Love package"
    if type == "blender":       return "Blender file"
    if type == "unknown":       return "Other"

    return "Unknown type"

class EntryPackage(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    url = db.Column(db.String(256))
    entry_id = db.Column(db.Integer, db.ForeignKey("entry.id"))
    type = db.Column(db.Enum(
        "web",      # Flash, html5, js...
        "linux",    # Linux binaries (e.g. *.tar.gz)
        "linux32",  # Linux32 binaries (e.g. *.tar.gz)
        "linux64",  # Linux64 binaries (e.g. *.tar.gz)
        "windows",  # Windows binaries (e.g. *.zip, *.exe)
        "windows32",# Windows32 binaries (e.g. *.zip, *.exe)
        "windows64",# Windows64 binaries (e.g. *.zip, *.exe)
        "mac",      # MacOS application packages
        "combi",    # Linux + Windows + Source (and more, optional)
        "love",     # Löve packages
        "blender",  # Blender save file (*.blend)
        "source",   # Source package (e.g. *.zip or *.tar.gz)
        "git",      # Version control repository: GIT
        "svn",      # Version control repository: SVN
        "hg",       # Version control repository: HG
        "unknown"))

    def __init__(self, entry, url, type = "unknown"):
        self.url = url
        self.type = type
        self.entry = entry

    def __repr__(self):
        return "<EntryPackage %r>" % self.id

    def typeString(self):
        return entry_package_type_string(self.type)

class EntryScreenshot(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    url = db.Column(db.String(256))
    caption = db.Column(db.Text)
    entry_id = db.Column(db.Integer, db.ForeignKey("entry.id"))

    def __init__(self, url, caption, entry):
        self.entry = entry
        self.url = url
        self.caption = caption

    def __repr__(self):
        return "<EntryScreenshot %r>" % self.id

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
