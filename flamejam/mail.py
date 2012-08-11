from flamejam import app
from flamejam.models import Participant
from flaskext.mail import Message
from flask import render_template

class Mail(object):
    def __init__(self, subject):
        self.recipients = []
        self.content = ""
        self.subject = subject

    def addRecipients(self, recipients):
        self.addRecipient(recipients)

    def addRecipient(self, recipient):
        t = type(recipient)
        if t is list:
            for r in recipient:
                self.addRecipients(r)
        elif t is Participant:
            self.addRecipient(recipient.email)
        elif t is str or str(recipient):
            self.recipients.append(str(recipient))
        else:
            raise Exception("Only User objects, email address strings or lists of these are allowed.")

    def setContent(self, content):
        self.content = content

    def render(self, template, *args, **kwargs):
        self.content = render_template(template, *args, **kwargs)


    def send(self):
        if not self.recipients:
            raise Exception("No email recipients set.")
        if not self.subject:
            raise Exception("No email subject set.")
        if not self.content:
            raise Exception("No email content set.")

        if app.config["MAIL_ENABLED"]:
            if not app.config["MAIL_SENDER"]:
                raise Exception("No email sender set in config (MAIL_SENDER).")

            with mail.connect() as connection:
                for recipient in self.recipients:
                    msg = Message(self.subject, recipients = [recipient], sender = app.config["MAIL_SENDER"])
                    msg.html = self.content
                    connection.send(msg)
        else:
            print "Sending mail to: "
            for p in self.recipients:
                print "  - " + p
            print "=" * 40
            print "Mail Content:"
            print "=" * 40
            print self.content
            print "=" * 40
