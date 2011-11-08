# -*- coding: utf-8 -*-

from operator import attrgetter
from datetime import datetime, timedelta
from hashlib import sha512, md5
from flamejam import app, db, filters
from flask import url_for, Markup
import re
import random

# rating:
# Participant <one2many> RatingSkip <many2one> Entry
# Participant <one2many> Rating <many2one> Entry

# Teams:
# Participant <many2many> Entry

team_members = db.Table('team_members',
    db.Column('entry_id', db.Integer, db.ForeignKey('entry.id')),
    db.Column('participant_id', db.Integer, db.ForeignKey('participant.id')),
)

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
    is_admin = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean)
    receive_emails = db.Column(db.Boolean)
    registered = db.Column(db.DateTime)
    entries = db.relationship('Entry', backref='participant', lazy='dynamic')
    team_entries = db.relationship("Entry",
                    secondary = team_members,
                    backref = "team")
    ratings = db.relationship('Rating', backref='participant', lazy='dynamic')
    comments = db.relationship('Comment', backref='participant', lazy='dynamic')
    jams = db.relationship('Jam', backref='author', lazy='dynamic')
    rating_skips = db.relationship('RatingSkip', backref='participant', lazy='dynamic')
    ratings = db.relationship('Rating', backref = 'participant', lazy='dynamic')

    def __init__(self, username, password, email, is_admin=False,
            is_verified=False, receive_emails = True):
        self.username = username
        self.password = sha512((password+app.config['SECRET_KEY']).encode('utf-8')).hexdigest()
        self.email = email
        self.is_admin = is_admin
        self.is_verified = is_verified
        self.registered = datetime.utcnow()
        self.receive_emails = receive_emails

    def getVerificationHash(self):
        # combine a few properties, hash md5
        # take first 8 chars for simplicity
        return md5(self.username + self.password + app.config['SECRET_KEY']).hexdigest()[:8]

    def skippedEntry(self, entry):
        return self.rating_skips.filter_by(entry = entry).first() != None

    def ratedEntry(self, entry):
        return self.ratings.filter_by(entry = entry).first() != None

    def getRatingCount(self, jam):
        i = 0
        for r in self.ratings:
            if r.entry.jam == jam:
                i += 1
        return i

    def getTotalEntryCount(self):
        return len(self.entries.all()) + len(self.team_entries)

    def getSkippedCount(self, jam):
        return len(self.rating_skips.filter(RatingSkip.participant_id == self.id and Entry.jam_id == jam.id).all())

    def __repr__(self):
        return '<User %r>' % self.username

    def url(self, **values):
        return url_for('show_participant', username = self.username, **values)

    def getAvatar(self, size = 32):
        return "http://www.gravatar.com/avatar/{0}?s={1}&d=retro".format(md5(self.email.lower()).hexdigest(), size)

    def getLink(self, class_ = ""):
        s = 14
        if self.is_admin:
            class_ += " admin"
        return Markup('<a class="user {4}" href="{0}"><img width="{2}" height="{2}" src="{3}" class="icon"/> {1}</a>'.format(
            self.url(), self.username, s, self.getAvatar(s), class_))

    def canRate(self, entry):
        return entry.participant != self and not self in entry.team

    def canEdit(self, entry):
        return entry.participant == self

    def getEntryInJam(self, jam):
        for entry in self.entries:
            if entry.jam == jam:
                return entry
        return None

    def getTeamEntryInJam(self, jam):
        for entry in self.team_entries:
            if entry.jam == jam:
                return entry
        return None

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

        return "Database error."

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
    team_jam = db.Column(db.Boolean)
    entries = db.relationship('Entry', backref='jam', lazy='dynamic')
    author_id = db.Column(db.Integer, db.ForeignKey('participant.id'))

    def __init__(self, title, author, start_time, end_time=None,
            packaging_deadline=None, voting_end=None, team_jam=False, theme = ''):
        self.title = title
        self.slug = get_slug(title)
        self.start_time = start_time
        self.theme = theme
        self.author = author
        self.team_jam = team_jam

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

    def url(self, **values):
        return url_for('show_jam', jam_slug = self.slug, **values)

    def getTopEntries(self):
        e = list(self.entries.all())
        e.sort(cmp = entryCompare)
        return e

    def getShuffledEntries(self):
        e = list(self.entries.all())
        random.shuffle(e)
        return e

def entryCompare(left, right):
    x = right.getTotalScore() - left.getTotalScore()
    if x > 0:
        return 1
    elif x < 0:
        return -1
    else:
        return 0

def participantTotalEntryCompare(left, right):
    x = right.getTotalEntryCount() - left.getTotalEntryCount()
    if x > 0:
        return 1
    elif x < 0:
        return -1
    else:
        return 0

class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128))
    slug = db.Column(db.String(128))
    description = db.Column(db.Text)
    posted = db.Column(db.DateTime)
    jam_id = db.Column(db.Integer, db.ForeignKey('jam.id'))
    participant_id = db.Column(db.Integer, db.ForeignKey('participant.id'))
    rating_skips = db.relationship('RatingSkip', backref='entry', lazy='dynamic')
    ratings = db.relationship('Rating', backref = 'entry', lazy='dynamic')
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
        return '<Entry %r>' % self.title

    def url(self, action = "", **values):
        return url_for("show_entry", jam_slug = self.jam.slug, entry_slug = self.slug, action = action, **values)

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
        jam_entries = list(self.jam.entries.all())
        jam_entries.sort(cmp = entryCompare)
        return jam_entries.index(self) + 1

def entry_package_type_string(type):
    if type == "web":           return "Web link (Flash etc.)"
    if type == "linux":         return "Binaries: Linux 32/64-bit"
    if type == "linux32":       return "Binaries: Linux 32-bit"
    if type == "linux64":       return "Binaries: Linux 64-bit"
    if type == "windows":       return "Binaries: Windows"
    if type == "windows64":     return "Binaries: Windows 64-bit"
    if type == "mac":           return "Binaries: MacOS Application"
    if type == "source":        return "Source: package"
    if type == "git":           return "Source: Git repository"
    if type == "svn":           return "Source: SVN repository"
    if type == "hg":            return "Source: HG repository"
    if type == "combi":         return "Combined package: Linux + Windows + Source (+ more, optional)"
    if type == "love":          return "Love package"
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
    entry_id = db.Column(db.Integer, db.ForeignKey('entry.id'))
    participant_id = db.Column(db.Integer, db.ForeignKey('participant.id'))

    def __init__(self, score_gameplay, score_graphics, score_audio, score_innovation,
        score_story, score_technical, score_controls, score_overall, text, entry, participant):
        self.score_gameplay = score_gameplay
        self.score_graphics = score_graphics
        self.score_audio = score_audio
        self.score_innovation = score_innovation
        self.score_story = score_story
        self.score_technical = score_technical
        self.score_controls = score_controls
        self.score_overall = score_overall
        self.text = text
        self.entry = entry
        self.participant = participant
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


class RatingSkip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reason = db.Column(db.Enum("platform", "uninteresting", "crash"))
    entry_id = db.Column(db.Integer, db.ForeignKey("entry.id"))
    participant_id = db.Column(db.Integer, db.ForeignKey("participant.id"))

    def __init__(self, participant, entry, reason):
        self.participant = participant
        self.entry = entry
        self.reason = reason

    def __repr__(self):
        return "<RatingSkip %r>" % self.id

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
