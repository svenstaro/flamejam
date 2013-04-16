# -*- coding: utf-8 -*-

from operator import attrgetter
from datetime import datetime, timedelta
from hashlib import sha512, md5
from flamejam import app, db, filters
from flask import url_for, Markup
import requests
import re
import random

# rating:
# User <one2many> RatingSkip <many2one> Game
# User <one2many> Rating <many2one> Game

# Teams:
# User <many2many> Game

def findLocation(loc):
#    try:
        r = requests.get("http://maps.googleapis.com/maps/api/geocode/json?address=%s&sensor=false&language=en" % loc)
        c = r.json()["results"][0]
        a = c["address_components"]

        city = ""
        state = ""
        region = ""
        flag = ""
        coords = "%s,%s" % (c["geometry"]["location"]["lat"], c["geometry"]["location"]["lng"])

        for comp in a:
            if comp["types"][0] == "locality": city = comp["long_name"]
            elif comp["types"][0] == "administrative_area_level_1": region = comp["long_name"]
            elif comp["types"][0] == "country":
                state = comp["long_name"]
                flag = comp["short_name"].lower()

        first = state

        if state == "United States" and region:
            first += ", " + region

        if city:
            first += ", " + city
        return first, coords, flag
#    except:
#        return None

def get_slug(s):
    s = s.lower()
    s = re.sub(r"[\s_+]+", "-", s)
    s = re.sub("[^a-z0-9\-]", "", s)
    return s


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(128))
    token = db.Column(db.Integer, nullable=True, default=None)
    email = db.Column(db.String(256), unique=True)
    new_email = db.Column(db.String(256), unique=True)
    is_admin = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean)
    is_deleted = db.Column(db.Boolean, default = False)
    registered = db.Column(db.DateTime)
    ratings = db.relationship('Rating', backref='user', lazy = "dynamic")
    comments = db.relationship('Comment', backref='user', lazy = "dynamic")
    rating_skips = db.relationship('RatingSkip', backref='user', lazy = "dynamic")
    devlog_posts = db.relationship("DevlogPost", backref = "author", lazy = "dynamic")
    invitations = db.relationship("Invitation", backref = "user", lazy = "dynamic")
    registrations = db.relationship("Registration", backref = "user", lazy = "dynamic")

    ability_programmer = db.Column(db.Boolean)
    ability_gamedesigner = db.Column(db.Boolean)
    ability_2dartist = db.Column(db.Boolean)
    ability_3dartist = db.Column(db.Boolean)
    ability_composer = db.Column(db.Boolean)
    ability_sounddesigner = db.Column(db.Boolean)
    abilities_extra = db.Column(db.String(128))
    location = db.Column(db.String(128))
    location_coords = db.Column(db.String(128))
    location_display = db.Column(db.String(128))
    location_flag = db.Column(db.String(16), default = "unknown")
    real_name = db.Column(db.String(128))
    about = db.Column(db.Text)
    website = db.Column(db.String(128))

    pm_mode = db.Column(db.Enum("email", "form", "disabled"), default = "form")

    notify_new_jam = db.Column(db.Boolean, default = True)
    notify_jam_start = db.Column(db.Boolean, default = True)
    notify_jam_finish = db.Column(db.Boolean, default = True)
    notify_game_comment = db.Column(db.Boolean, default = True)
    notify_team_changes = db.Column(db.Boolean, default = True)
    notify_game_changes = db.Column(db.Boolean, default = True)
    notify_team_invitation = db.Column(db.Boolean, default = True)
    notify_newsletter = db.Column(db.Boolean, default = True)

    def __init__(self, username, password, email, is_admin = False, is_verified = False, receive_emails = True):
        self.username = username
        self.password = sha512((password+app.config['SECRET_KEY']).encode('utf-8')).hexdigest()
        self.email = email
        self.new_email = email
        self.is_admin = is_admin
        self.is_verified = is_verified
        self.registered = datetime.utcnow()
        self.receive_emails = receive_emails

    def getVerificationHash(self):
        # combine a few properties, hash md5
        # take first 8 chars for simplicity
        # make it email specific
        return md5(self.username + self.new_email + self.password + app.config['SECRET_KEY']).hexdigest()[:8]

    def getResetToken(self):
        # combine a few properties, hash md5
        # take first 8 chars for simplicity
        return md5(str(self.token) + app.config['SECRET_KEY']).hexdigest()[:8]

    def skippedGame(self, game):
        return self.rating_skips.filter_by(game = game).first() != None

    def ratedGame(self, game):
        return self.ratings.filter_by(game = game).first() != None

    def getRatingCount(self, jam):
        i = 0
        for r in self.ratings:
            if r.game.jam == jam:
                i += 1
        return i

    def getTotalGameCount(self):
        i = 0
        for r in self.registrations:
            if r.team:
                i += r.team.games.count()
        return i

    def getSkippedCount(self, jam):
        return len(self.rating_skips.filter(RatingSkip.user_id == self.id and Game.jam_id == jam.id).all())

    def __repr__(self):
        return '<User %r>' % self.username

    def url(self, **values):
        return url_for('show_user', username = self.username, **values)

    def getAvatar(self, size = 32):
        return "http://www.gravatar.com/avatar/{0}?s={1}&d=identicon".format(md5(self.email.lower()).hexdigest(), size)

    def getLocation(self):
        return Markup('<span class="flag %s"></span> %s' % (self.location_flag, self.location_display or "n/a"))

    def getLink(self, class_ = ""):
        if self.is_deleted:
            return Markup('<span class="user deleted">[DELETED]</span>')

        s = 16
        if self.is_admin:
            class_ += " admin"
        return Markup('<a class="user {4}" href="{0}"><img width="{2}" height="{2}" src="{3}" class="icon"/> {1}</a>'.format(
            self.url(), self.username, s, self.getAvatar(s), class_))

    @property
    def abilities(self):
        a = []
        if self.ability_programmer:
            a.append("Programming")
        if self.ability_gamedesigner:
            a.append("Game Design")
        if self.ability_2dartist:
            a.append("Graphics / 2D Art")
        if self.ability_3dartist:
            a.append("Modelling / 3D Art")
        if self.ability_composer:
            a.append("Composing")
        if self.ability_sounddesigner:
            a.append("Sound Design")
        return a

    def getRegistration(self, jam):
        return Registration.query.filter_by(user_id = self.id, jam_id = jam.id).first()

    def getTeam(self, jam):
        return self.getRegistration(jam).team

    def inTeam(self, team):
        return self in team.members

    def canRate(self, game):
        return not self.inTeam(game.team)

    def canEdit(self, game):
        return self.inTeam(game.team)

    def joinJam(self, jam, generateTeam = True):
        r = Registration(self, jam)
        db.session.add(r)
        db.session.commit() # need to commit so the team does not register us automatically

        if generateTeam:
            t = Team(self, jam)
            db.session.add(t)

        db.session.commit()

    def leaveJam(self, jam):
        # leave team
        if self.getTeam(jam):
            self.getTeam(jam).userLeave(self) #  will destroy the team if then empty

        # delete registration
        if self.getRegistration(jam):
            db.session.delete(self.getRegistration(jam))

class JamStatusCode(object):
    ANNOUNCED    = 0
    REGISTRATION = 1
    RUNNING      = 2
    PACKAGING    = 3
    RATING       = 4
    FINISHED     = 5

class JamStatus(object):
    def __init__(self, code, time):
        self.code = code
        self.time = time

    def __repr__(self):
        t = filters.formattime(self.time)
        d = filters.humandelta(datetime.utcnow(), self.time)
        if self.code == JamStatusCode.ANNOUNCED:
            return "Announced for {0}".format(t)
        elif self.code == JamStatusCode.REGISTRATION:
            return "Registrations until {0}".format(t)
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
    team_limit = db.Column(db.Integer) # 0 = no limit
    games = db.relationship('Game', backref="jam", lazy = "dynamic")
    registrations = db.relationship("Registration", backref = "jam", lazy = "dynamic")
    teams = db.relationship("Team", backref = "jam", lazy = "dynamic")
    announcements = db.relationship("Announcement", backref = "jam", lazy = "dynamic")

    description = db.Column(db.Text)
    restrictions = db.Column(db.Text)

    registration_duration = db.Column(db.Integer) # hours
    packaging_duration = db.Column(db.Integer) # hours
    rating_duration = db.Column(db.Integer) # hours
    duration = db.Column(db.Integer) # hours

    last_notification_sent = db.Column(db.Integer, default = -1) # last notification that was sent, e.g. 0 = announcement, 1 = registration, (see status codes)

    def __init__(self, title, start_time, duration = 48, team_limit = 0, theme = ''):
        self.title = title
        self.slug = get_slug(title)
        self.start_time = start_time
        self.duration = duration
        self.registration_duration = 24 * 14
        self.packaging_duration = 24 * 1
        self.rating_duration = 24 * 5
        self.announced = datetime.utcnow()
        self.theme = theme
        self.team_limit = team_limit

    @property
    def participants(self):
        p = []
        for r in self.registrations:
            p.append(r.user)
        return p

    @property
    def end_time(self):
        return self.start_time + timedelta(hours = self.duration)

    @property
    def packaging_deadline(self):
        return self.end_time + timedelta(hours = self.packaging_duration)

    @property
    def rating_end(self):
        return self.packaging_deadline + timedelta(hours = self.rating_duration)

    @property
    def registration_start(self):
        return self.start_time - timedelta(hours = self.registration_duration)

    def __repr__(self):
        return '<Jam %r>' % self.slug

    def getStatus(self):
        now = datetime.utcnow()
        if self.registration_start > now:
            return JamStatus(JamStatusCode.ANNOUNCED, self.start_time)
        elif self.start_time > now:
            return JamStatus(JamStatusCode.REGISTRATION, self.start_time)
        elif self.end_time > now:
            return JamStatus(JamStatusCode.RUNNING, self.end_time)
        elif self.packaging_deadline > now:
            return JamStatus(JamStatusCode.PACKAGING, self.packaging_deadline)
        elif self.rating_end > now:
            return JamStatus(JamStatusCode.RATING, self.rating_end)
        else:
            return JamStatus(JamStatusCode.FINISHED, self.end_time)

    def url(self, **values):
        return url_for('jam_info', jam_slug = self.slug, **values)

    def getTopGames(self):
        e = list(self.games.all())
        e.sort(cmp = gameCompare)
        return e

    def getShuffledGames(self):
        e = list(self.games.all())
        random.shuffle(e)
        return e

def gameCompare(left, right):
    x = right.getTotalScore() - left.getTotalScore()
    if x > 0:
        return 1
    elif x < 0:
        return -1
    else:
        return 0

def userTotalGameCompare(left, right):
    x = right.getTotalGameCount() - left.getTotalGameCount()
    if x > 0:
        return 1
    elif x < 0:
        return -1
    else:
        return 0

class Registration(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"))
    jam_id = db.Column(db.Integer, db.ForeignKey("jam.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    show_in_finder = db.Column(db.Boolean, default = True)
    registered = db.Column(db.DateTime)

    def __init__(self, user, jam, show_in_finder = True):
        self.user = user
        self.jam = jam
        self.show_in_finder = show_in_finder
        self.registered = datetime.utcnow()

class DevlogPost(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"))
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    title = db.Column(db.String(128))
    content = db.Column(db.Text)
    posted = db.Column(db.DateTime)

    def __init__(self, team, author, title, content):
        self.team = team
        self.author = author
        self.title = title
        self.content = content
        self.posted = datetime.utcnow()

class Team(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    jam_id = db.Column(db.Integer, db.ForeignKey("jam.id"))
    name = db.Column(db.String(80))

    wip = db.Column(db.String(128))
    livestreams = db.Column(db.Text) # list of livestreams, one URL per file
    irc = db.Column(db.String(128))

    registrations = db.relationship("Registration", backref = "team", lazy = "dynamic")
    devlog_posts = db.relationship("DevlogPost", backref = "team", lazy = "dynamic")
    invitations = db.relationship("Invitation", backref = "team", lazy = "dynamic")
    games = db.relationship("Game", backref = "team", lazy = "dynamic")

    def __init__(self, user, jam):
        self.jam = jam
        self.userJoin(user)

        number = 1
        while Team.query.filter_by(jam_id = jam.id, name = "Team " + str(number)).first():
            number += 1
        self.name = "Team " + str(number)

    @property
    def members(self):
        m = []
        for r in self.registrations:
            m.append(r.user)
        return m

    @property
    def isSingleTeam(self):
        return self.registrations.count() == 1

    def url(self, **values):
        return url_for("jam_team", jam_slug = self.jam.slug, team_id = self.id, **values)

    def userJoin(self, user):
        r = user.getRegistration(self.jam)
        if not r:
            # register user, but do not create automatic team, we don't need
            # that anyway
            user.joinJam(self.jam, False)
        elif r in self.registrations:
            return # user is already in this team
        elif r.team and r.team != self:
            r.team.userLeave(user)

        r.team = self
        db.session.commit()

    def userLeave(self, user):
        r = user.getRegistration(self.jam)

        if r.team != self:
            return # not in this team, nevermind ;)

        if self.isSingleTeam:
            # only user in team, we can destroy this team
            self.destroy()

        r.team = None
        db.session.commit()

    def destroy(self):
        # also destroy all the games, invitations and devlog posts
        for game in self.games:
            game.destroy()
        for invitation in self.invitations:
            db.session.delete(invitation)
        for post in self.devlog_posts:
            db.session.delete(post)
        db.session.delete(self)

    def getInvitation(self, user):
        return Invitation.query.filter_by(user_id = user.id, team_id = self.id).first()

    def inviteUser(self, user, sender): # sender: which user sent the invitation
        from flamejam.mail import Mail

        if self.getInvitation(user): i = self.getInvitation(user) # already invited
        else: i = Invitation(self, user)
        db.session.add(i)
        db.session.commit()

        # send email
        m = Mail("BaconGameJam Team Invitation")
        m.render("emails/jam/invitation.html", team = self, sender = sender, recipient = user, invitation = i)
        m.addRecipient(user)
        m.send()
        return i

class Invitation(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    def __init__(self, team, user):
        self.team = team
        self.user = user

    def url(self, **values):
        return url_for("invitation", id = self.id, _external = True, **values)

    def accept(self):
        self.team.userJoin(self.user)
        db.session.delete(self)
        db.session.commit()

    def decline(self):
        db.session.delete(self)
        db.session.commit()

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128))
    slug = db.Column(db.String(128))
    description = db.Column(db.Text)
    created = db.Column(db.DateTime)
    jam_id = db.Column(db.Integer, db.ForeignKey('jam.id'))
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    rating_skips = db.relationship('RatingSkip', backref='game', lazy = "dynamic")
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
        # destroy all ratings, rating skips, comments, packages, screenshots
        for rating in self.ratings:
            db.session.delete(rating)
        for skip in self.rating_skips:
            db.session.delete(skip)
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

def game_package_type_string(type):
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

class GamePackage(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    url = db.Column(db.String(256))
    game_id = db.Column(db.Integer, db.ForeignKey("game.id"))
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

    def __init__(self, game, url, type = "unknown"):
        self.url = url
        self.type = type
        self.game = game

    def __repr__(self):
        return "<GamePackage %r>" % self.id

    def typeString(self):
        return game_package_type_string(self.type)

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


class RatingSkip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reason = db.Column(db.Enum("platform", "uninteresting", "crash"))
    game_id = db.Column(db.Integer, db.ForeignKey("game.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    def __init__(self, user, game, reason):
        self.user = user
        self.game = game
        self.reason = reason

    def __repr__(self):
        return "<RatingSkip %r>" % self.id

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
        return '<Comment %r>' % self.id


class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    subject = db.Column(db.String(128))
    message = db.Column(db.Text)
    posted = db.Column(db.DateTime)
    context = db.Column(db.Enum("new_jam", "registration_start", "jam_start",
        "packaging_start", "rating_start", "jam_finished", "newsletter"),
        default = "newsletter")
    jam_id = db.Column(db.Integer, db.ForeignKey('jam.id'))

    def __init__(self, message):
        self.message = message
        self.posted = datetime.utcnow()

    def __repr__(self):
        return '<Announcement %r>' % self.id

    def sendMail(self):
        users = []

        if self.context == "newsletter":
            users = User.query.filter_by(notify_newsletter = True).all()
        elif self.jam:
            if self.context in ("new_jam", "registration_start"):
                users = User.query.filter_by(notify_new_jam = True).all()
            elif self.context in ("jam_start", "packaging_start", "rating_start"):
                users = User.query.filter_by(notify_jam_start = True).all()
            elif self.context == "jam_finished":
                users = User.query.filter_by(notify_jam_finish = True).all()

            u2 = []
            for user in users:
                if user.getRegistration(self.jam):
                    u2.append(user)
            users = u2
        else:
            raise Error('Announcement needs a jam or context "newsletter".')

        # new_jam, registration_start, jam_start, packaging_start, rating_start, jam_finished, newsletter

        from flamejam.mail import Mail
        for user in users:
            m = Mail(("BaconGameJam Newsletter - " if self.context == "newsletter" else "") + self.subject)
            m.render("emails/announcements/%s.html" % self.context, recipient = user, jam = self.jam, subject = self.subject, message = self.message)
            m.addRecipient(user)
            m.send()
