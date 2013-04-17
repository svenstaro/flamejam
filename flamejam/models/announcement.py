# -*- coding: utf-8 -*-

from flamejam import app, db
from datetime import datetime

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
