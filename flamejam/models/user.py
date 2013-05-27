# -*- coding: utf-8 -*-

from flamejam import app, db, login_manager
from flamejam.utils import hash_password, verify_password, findLocation
from flamejam.models import Registration, Team, Game
from flask import url_for, Markup
from datetime import datetime
from hashlib import md5
import scrypt

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.LargeBinary())
    token = db.Column(db.BigInteger, nullable=True, default=None)
    email = db.Column(db.String(191), unique=True)
    new_email = db.Column(db.String(191), unique=True)
    is_admin = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean)
    is_deleted = db.Column(db.Boolean, default = False)
    registered = db.Column(db.DateTime)
    ratings = db.relationship('Rating', backref='user', lazy = "dynamic")
    comments = db.relationship('Comment', backref='user', lazy = "dynamic")
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
    notify_team_invitation = db.Column(db.Boolean, default = True)
    notify_newsletter = db.Column(db.Boolean, default = True)

    def __init__(self, username, password, email, is_admin = False, is_verified = False):
        self.username = username
        self.password = hash_password(password)
        self.email = email
        self.new_email = email
        self.is_admin = is_admin
        self.is_verified = is_verified
        self.registered = datetime.utcnow()

    def __repr__(self):
        return '<User %r>' % self.username

    def get_id(self):
        return self.id

    def is_active(self):
        return self.is_verified

    def is_anonymous(self):
        return False

    def is_authenticated(self):
        return True

    def getVerificationHash(self):
        # combine a few properties, hash it
        # take first 16 chars for simplicity
        # make it email specific
        hash = scrypt.hash(str(self.username) + str(self.new_email), app.config['SECRET_KEY'])
        return hash.encode('hex')[:16]

    def getResetToken(self):
        # combine a few properties, hash it
        # take first 16 chars for simplicity
        hash = scrypt.hash(str(self.token), app.config['SECRET_KEY'])
        return hash.encode('hex')[:16]

    def ratedGame(self, game):
        return self.ratings.filter_by(game = game).first() != None

    def getRatingCount(self, jam):
        i = 0
        for r in self.ratings:
            if r.game.jam == jam:
                i += 1
        return i

    @property
    def games(self):
        g = []
        for r in self.registrations:
            if r.team:
                for game in r.team.games:
                    g.append(game)

        import operator
        g.sort(key = operator.attrgetter("created"))

        return g

    def url(self, **values):
        return url_for('show_user', username = self.username, **values)

    def getAvatar(self, size = 32):
        return "http://www.gravatar.com/avatar/{0}?s={1}&d=identicon".format(md5(self.email.lower()).hexdigest(), size)

    def setLocation(self, location):
        if not location:
            self.location = ""
            self.location_display = ""
            self.location_coords = ""
            self.location_flag = "unknown"
            return True

        new_loc, new_coords, new_flag = findLocation(location)
        if not new_loc:
            return False
        self.location = location
        self.location_display = new_loc
        self.location_coords = new_coords
        self.location_flag = new_flag
        return True

    def getLocation(self):
        return Markup('<span class="location"><span class="flag %s"></span> <span class="city">%s</span></span>' % (self.location_flag, self.location_display or "n/a"))

    def getLink(self, class_ = "", real = True):
        if self.is_deleted:
            return Markup('<span class="user deleted">[DELETED]</span>')

        s = 16
        if self.is_admin:
            class_ += " admin"

        link = ''
        link += '<a class="user {0}" href="{1}">'.format(class_, self.url())
        link += '<img width="{0}" height="{0}" src="{1}" class="icon"/> '.format(s, self.getAvatar(s))
        link += '<span class="name"><span class="username">{0}</span>'.format(self.username)
        link += ' <span class="real">({0})</span>'.format(self.real_name) if self.real_name and real else ''
        link += '</span></a>'

        return Markup(link)

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

    def abilityString(self):
        a = ", ".join(self.abilities)
        if self.abilities_extra:
            a += '<div class="ability-extra">' + self.abilities_extra + '</div>'
        return a

    def getRegistration(self, jam):
        return Registration.query.filter_by(user_id = self.id, jam_id = jam.id).first()

    def getTeam(self, jam):
        r = self.getRegistration(jam)
        return r.team if r and r.team else None

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
            self.generateTeam(jam)
        else:
            db.session.commit()

    def generateTeam(self, jam):
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

    def numberOfGames(self):
        return len(self.games)

# we need this so Flask-Login can load a user into a session
@login_manager.user_loader
def load_user(user_id):
    user = User.query.filter_by(id=user_id).first()
    if user:
        return user
    else:
        return None
