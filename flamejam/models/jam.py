from flamejam import app, db, mail
from flamejam.utils import get_slug
from flamejam.filters import formattime, humandelta
from flamejam.models.game import Game
from flamejam.models.gamepackage import GamePackage
from datetime import datetime, timedelta
from flask import url_for, Markup, render_template
from flask_mail import Message
from smtplib import SMTPRecipientsRefused


class Jam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(128), unique=True)
    title = db.Column(db.String(128), unique=True)
    theme = db.Column(db.String(128))
    announced = db.Column(db.DateTime)  # Date on which the jam was announced
    start_time = db.Column(db.DateTime)  # The jam starts at this moment
    team_limit = db.Column(db.Integer)  # 0 = no limit
    games = db.relationship('Game', backref="jam", lazy="subquery")
    participations = db.relationship("Participation", backref="jam", lazy="subquery")
    teams = db.relationship("Team", backref="jam", lazy="subquery")

    description = db.Column(db.Text)
    restrictions = db.Column(db.Text)

    registration_duration = db.Column(db.Integer)  # hours
    packaging_duration = db.Column(db.Integer)  # hours
    rating_duration = db.Column(db.Integer)  # hours
    duration = db.Column(db.Integer)  # hours

    # last notification that was sent, e.g. 0 = announcement, 1 = registration, (see status codes)
    last_notification_sent = db.Column(db.Integer, default=-1)

    def __init__(self, title, start_time, duration=48, team_limit=0, theme=''):
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
        return [r.user for r in self.participations]

    @property
    def end_time(self):
        return self.start_time + timedelta(hours=self.duration)

    @property
    def packaging_deadline(self):
        return self.end_time + timedelta(hours=self.packaging_duration)

    @property
    def rating_end(self):
        return self.packaging_deadline + timedelta(hours=self.rating_duration)

    @property
    def registration_start(self):
        return self.start_time - timedelta(hours=self.registration_duration)

    def __repr__(self):
        return f"<Jam {self.slug}>"

    def get_status(self):
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

    def url(self, **kwargs):
        return url_for('jam_info', jam_slug=self.slug, **kwargs)

    def games_filtered_by_package_types(self, filters):
        games = Game.query.filter_by(is_deleted=False).filter_by(jam_id=self.id)
        if filters == set():
            games = games
        elif 'packaged' in filters:
            games = games.join(GamePackage)
        else:
            games = games.filter(GamePackage.type.in_(filters)).join(GamePackage)
        return games.all()

    def games_by_score(self, filters=set()):
        e = self.games_filtered_by_package_types(filters)
        e.sort(key=Game.score.fget, reverse=True)
        return e

    def games_by_total_ratings(self, filters=set()):
        e = self.games_filtered_by_package_types(filters)
        e.sort(key=Game.number_ratings.fget)
        return e

    @property
    def show_theme(self):
        return self.get_status().code >= JamStatusCode.RUNNING and self.theme

    @property
    def show_ratings(self):
        return self.get_status().code == JamStatusCode.FINISHED

    def get_link(self):
        s = f'<a class="jam" href="{self.url()}">{self.title}</a>'
        if self.show_theme:
            s += f' <span class="theme">{self.theme}</span>'
        return Markup(s)

    def send_all_notifications(self):
        last = -1
        for n in range(self.last_notification_sent + 1, self.get_status().code + 1):
            if self.send_notification(n):
                last = n
        return last

    def send_notification(self, n):
        if not JamStatusCode.ANNOUNCED <= n <= JamStatusCode.FINISHED:
            return False

        kwargs = {}

        if n == JamStatusCode.ANNOUNCED:
            template = "announcement"
            notify = "new_jam"
            subject = f"Jam announced: {self.title}"
        elif n == JamStatusCode.REGISTRATION:
            template = "registration_start"
            notify = "new_jam"
            subject = f"Registrations for {self.title} now open"
        elif n == JamStatusCode.RUNNING:
            template = "start"
            notify = "jam_start"
            subject = f"{self.title} starts now!"
        elif n == JamStatusCode.PACKAGING:
            template = "packaging_start"
            notify = "jam_finish"
            subject = f"{self.title} is over"
        elif n == JamStatusCode.RATING:
            template = "rating_start"
            notify = "jam_finish"
            subject = f"Rating for {self.title} starts now"
        elif n == JamStatusCode.FINISHED:
            template = "finished"
            notify = "jam_finish"
            subject = f"Rating for {self.title} finished - Winners"
            kwargs = {"games": self.games_by_score()[:3]}

        if n >= JamStatusCode.RUNNING and n != JamStatusCode.RATING:
            users = [r.user for r in self.participations]
        else:
            from flamejam.models.user import User
            users = User.query.all()

        # Set this first because we might send for longer than a minute at which point the
        # next tick will come around.
        self.last_notification_sent = n
        db.session.commit()

        subject = app.config["LONG_NAME"] + ": " + subject

        with mail.connect() as conn:
            for user in users:
                if getattr(user, "notify_" + notify):
                    body = render_template("emails/jam/" + template + ".txt",
                                           recipient=user, jam=self, **kwargs)
                    sender = app.config['MAIL_DEFAULT_SENDER']
                    recipients = [user.email]
                    message = Message(subject=subject, sender=sender,
                                      body=body, recipients=recipients)
                    try:
                        conn.send(message)
                    except SMTPRecipientsRefused:
                        pass
        return True

    @property
    def livestream_teams(self):
        return [t for t in self.teams if t.livestream]


class JamStatusCode(object):
    ANNOUNCED = 0
    REGISTRATION = 1
    RUNNING = 2
    PACKAGING = 3
    RATING = 4
    FINISHED = 5


class JamStatus(object):
    def __init__(self, code, time):
        self.code = code
        self.time = time

    def __repr__(self):
        t = formattime(self.time)
        d = humandelta(datetime.utcnow(), self.time)
        if self.code == JamStatusCode.ANNOUNCED:
            return f"Announced for {t}"
        elif self.code == JamStatusCode.REGISTRATION:
            return f"Registrations until {t}"
        elif self.code == JamStatusCode.RUNNING:
            return f"Running until {t} ({d} left)"
        elif self.code == JamStatusCode.PACKAGING:
            return f"Packaging until {t} ({d} left)"
        elif self.code == JamStatusCode.RATING:
            return f"Rating until {t} ({d} left)"
        elif self.code == JamStatusCode.PACKAGING:
            return f"Finished since {t}"

        return "Database error."
