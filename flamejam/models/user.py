from flamejam import app, db, login_manager
from flamejam.utils import hash_password, find_location
from flamejam.models.participation import Participation
from flamejam.models.team import Team
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
    is_deleted = db.Column(db.Boolean, default=False)
    registered = db.Column(db.DateTime)
    ratings = db.relationship('Rating', backref='user', lazy="dynamic")
    comments = db.relationship('Comment', backref='user', lazy="dynamic")
    invitations = db.relationship("Invitation", backref="user", lazy="dynamic")
    participations = db.relationship("Participation", backref=db.backref("user", lazy="joined"),
                                     lazy="subquery")

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
    location_flag = db.Column(db.String(16), default="unknown")
    real_name = db.Column(db.String(128))
    about = db.Column(db.Text)
    website = db.Column(db.String(128))
    avatar = db.Column(db.String(128))

    pm_mode = db.Column(db.Enum("email", "form", "disabled"), default="form")

    notify_new_jam = db.Column(db.Boolean, default=True)
    notify_jam_start = db.Column(db.Boolean, default=True)
    notify_jam_finish = db.Column(db.Boolean, default=True)
    notify_game_comment = db.Column(db.Boolean, default=True)
    notify_team_invitation = db.Column(db.Boolean, default=True)
    notify_newsletter = db.Column(db.Boolean, default=True)

    def __init__(self, username, password, email, is_admin=False, is_verified=False):
        self.username = username
        self.password = hash_password(password)
        self.email = email
        self.new_email = email
        self.is_admin = is_admin
        self.is_verified = is_verified
        self.registered = datetime.utcnow()

    @property
    def is_active(self):
        return self.is_verified

    @property
    def is_anonymous(self):
        return False

    @property
    def is_authenticated(self):
        return True

    def __repr__(self):
        return f"<User {self.username}>"

    def get_id(self):
        return self.id

    def get_verification_hash(self):
        # combine a few properties, hash it
        # take first 16 chars for simplicity
        # make it email specific
        hash = scrypt.hash(str(self.username) + str(self.new_email), app.config['SECRET_KEY'])
        return hash.hex()[:16]

    def get_reset_token(self):
        # combine a few properties, hash it
        # take first 16 chars for simplicity
        hash = scrypt.hash(str(self.token), app.config['SECRET_KEY'])
        return hash.hex()[:16]

    def rated_game(self, game):
        return self.ratings.filter_by(game=game).first() is not None

    def get_rating_count(self, jam):
        i = 0
        for r in self.ratings:
            if r.game.jam == jam:
                i += 1
        return i

    @property
    def games(self):
        g = []
        for p in self.participations:
            if p.team:
                for game in p.team.games:
                    if not game.is_deleted:
                        g.append(game)

        import operator
        g.sort(key=operator.attrgetter("created"))

        return g

    def url(self, **kwargs):
        return url_for('show_user', username=self.username, **kwargs)

    def get_avatar(self, size=32):
        if self.avatar:
            return self.avatar.replace("%s", str(size))
        return "//gravatar.com/avatar/{0}?s={1}&d=identicon".format(
            md5(self.email.lower().encode('ASCII')).hexdigest(), size)

    def set_location(self, location):
        if not location:
            self.location = ""
            self.location_display = ""
            self.location_coords = ""
            self.location_flag = "unknown"
            return True

        new_loc, new_coords, new_flag = find_location(location)
        if not new_loc:
            return False
        self.location = location
        self.location_display = new_loc
        self.location_coords = new_coords
        self.location_flag = new_flag
        return True

    def get_location(self):
        display = self.location_display or "n/a"
        markup = f'<span class="location"><span class="flag {self.location_flag}"></span>'
        markup += f'<span class="city">{display}</span></span>'
        return Markup(markup)

    def get_link(self, class_="", real=True, avatar=True):
        if self.is_deleted:
            return Markup('<span class="user deleted">[DELETED]</span>')

        s = 16
        if self.is_admin:
            class_ += " admin"

        link = ''
        link += f'<a class="user {class_}" href="{self.url()}">'
        if avatar:
            link += f'<img width="{s}" height="{s}" src="{self.get_avatar(s)}" class="icon"/> '
        link += f'<span class="name"><span class="username">{self.username}</span>'
        if self.real_name and real:
            link += f' <span class="real">({self.real_name})</span>'
        else:
            link += ''
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

    def ability_string(self):
        a = ", ".join(self.abilities)
        if self.abilities_extra:
            a += f'<div class="ability-extra">{self.abilities_extra}</div>'
        return a

    def get_participation(self, jam):
        return Participation.query.filter_by(user_id=self.id, jam_id=jam.id).first()

    def get_team(self, jam):
        p = self.get_participation(jam)
        return p.team if p and p.team else None

    def in_team(self, team):
        return self in team.members

    def can_rate(self, game):
        return not self.in_team(game.team)

    def can_edit(self, game):
        return self.in_team(game.team)

    def join_jam(self, jam, generate_team=True):
        p = Participation(self, jam)
        db.session.add(p)
        db.session.commit()  # need to commit so the team does not register us automatically

        if generate_team:
            self.generate_team(jam)
        else:
            db.session.commit()

    def generate_team(self, jam):
        t = Team(self, jam)
        db.session.add(t)
        db.session.commit()

    def leave_jam(self, jam):
        # leave team
        if self.get_team(jam):
            self.get_team(jam).user_leave(self)  # will destroy the team if then empty

        # delete registration
        if self.get_participation(jam):
            db.session.delete(self.get_participation(jam))

    def number_of_games(self):
        return len(self.games)

    @property
    def open_invitations(self):
        invitations = []
        for invitation in self.invitations:
            if invitation.can_accept():
                invitations.append(invitation)
        return invitations


# we need this so Flask-Login can load a user into a session
@login_manager.user_loader
def load_user(user_id):
    user = User.query.filter_by(id=user_id).first()
    if user:
        return user
    else:
        return None
