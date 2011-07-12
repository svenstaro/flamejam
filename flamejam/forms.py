# -*- coding: utf-8 -*-

from flaskext.wtf import BaseForm, Form, TextField, TextAreaField, PasswordField,\
        DateTimeField, SubmitField, SelectField, HiddenField, BooleanField
from flaskext.wtf import Required, Length, EqualTo, Optional, NumberRange, Email,\
        ValidationError, URL
from flaskext.wtf.html5 import IntegerField, EmailField
import re
from hashlib import sha512
from flamejam import app, models

############## VALIDATORS ####################

class Not(object):
    def __init__(self, call, message = None):
        self.call = call
        self.message = message

    def __call__(self, form, field):
        errored = False
        try:
            self.call(form, field)
        except ValidationError:
            # there was an error, so don't do anything
            errored = True

        if not errored:
            raise ValidationError(self.call.message if self.message == None else self.message)

class MatchesRegex(object):
    def __init__(self, regex, message = "This field matches the regex {0}"):
        self.regex = regex
        self.message = message

    def __call__(self, form, field):
        if re.match(self.regex, field.data):
            raise ValidationError(self.message.format(self.regex))

class UsernameExists(object):
    def __call__(self, form, field):
        u = models.Participant.query.filter_by(username = field.data).first()
        if not u:
            raise ValidationError("The username does not exist.")

class LoginValidator(object):
    def __init__(self, pw_field, message_username = "The username is incorrect.", message_password = "The password is incorrect."):
        self.pw_field = pw_field
        self.message_username = message_username
        self.message_password = message_password

    def __call__(self, form, field):
        u = models.Participant.query.filter_by(username = field.data).first()
        if not u:
            raise ValidationError(self.message_username)
        elif u.password != sha512(form[self.pw_field].data).hexdigest():
            raise ValidationError(self.message_password)

############## FORMS ####################

class ParticipantLogin(Form):
    username = TextField("Username", validators=[LoginValidator("password")])
    password = PasswordField("Password", validators = [])

class ParticipantRegistration(Form):
    username = TextField("Username", validators=[
        MatchesRegex("[^0-9a-zA-Z\-_]", "Your username contains invalid characters. Only use alphanumeric characters, dashes and underscores."),
        Not(UsernameExists(), message = "That username already exists."),
        Length(min=6, max=80, message="You have to enter a username of 6 to 80 characters length.")])
    password = PasswordField("Password", validators=[Length(min=8, message = "Please enter a password of at least 8 characters.")])
    password2 = PasswordField("Password, again", validators=[EqualTo("password", "Passwords do not match.")])
    email = EmailField("Email", validators=[Email(message = "The email address you entered is invalid.")])
    # Also use recaptcha here
    receive_emails = BooleanField("I want to receive email notifications.", default = True)

class NewJam(Form):
    title = TextField("Jam title", validators=[Required(), Length(max=128)])
    start_time = DateTimeField("Start time",
            format="%Y-%m-%d %H:%M", validators=[Required()])
    # Add remaining fields

class SubmitEditEntry(Form):
    title = TextField("Entry title", validators=[Required(), Length(max=128)])
    description = TextAreaField("Description", validators=[Required()])

class EntryAddScreenshot(Form):
    url = TextField("URL", validators = [Required(), URL()])
    caption = TextField("Caption", validators = [Required()])

class EntryAddTeamMember(Form):
    username = TextField("Username:", validators = [Required(), UsernameExists()])

from models import entry_package_type_string

class EntryAddPackage(Form):
    url = TextField("URL", validators = [Required()])
    type = SelectField("Type", choices = [
        ("web",          entry_package_type_string("web")),
        ("linux",        entry_package_type_string("linux")),
        ("linux32",      entry_package_type_string("linux32")),
        ("linux64",      entry_package_type_string("linux64")),
        ("windows",      entry_package_type_string("windows")),
        ("windows64",    entry_package_type_string("windows64")),
        ("mac",          entry_package_type_string("mac")),
        ("source",       entry_package_type_string("source")),
        ("git",          entry_package_type_string("git")),
        ("svn",          entry_package_type_string("svn")),
        ("hg",           entry_package_type_string("hg")),
        ("combi",        entry_package_type_string("combi")),
        ("love",         entry_package_type_string("love")),
        ("blender",      entry_package_type_string("blender")),
        ("unknown",      entry_package_type_string("unknown"))])

class RateEntry(Form):
    entry_id = HiddenField(validators = [Required(), NumberRange(min = 1)])
    score_gameplay = IntegerField("Gameplay rating", validators=[Required(), NumberRange(min=1, max=10)], default = 5)
    score_graphics = IntegerField("Graphics rating", validators=[Required(), NumberRange(min=1, max=10)], default = 5)
    score_audio = IntegerField("Audio rating", validators=[Required(), NumberRange(min=1, max=10)], default = 5)
    score_innovation = IntegerField("Innovation rating", validators=[Required(), NumberRange(min=1, max=10)], default = 5)
    score_story = IntegerField("Story rating", validators=[Required(), NumberRange(min=1, max=10)], default = 5)
    score_technical = IntegerField("Technical rating", validators=[Required(), NumberRange(min=1, max=10)], default = 5)
    score_controls = IntegerField("Controls rating", validators=[Required(), NumberRange(min=1, max=10)], default = 5)
    score_overall = IntegerField("Overall rating", validators=[Required(), NumberRange(min=1, max=10)], default = 5)
    note = TextField("Additional notes", validators=[Optional()])

class SkipRating(Form):
    entry_id = HiddenField(validators = [Required(), NumberRange(min = 1)])
    reason = SelectField("Reason to skip", choices = [
        ("platform", "Platform not supported"),
        ("uninteresting", "Not interested"),
        ("crash", "Game crashed on start")
    ])

class WriteComment(Form):
    text = TextAreaField("Comment", validators=[Required(), Length(max=65535)])
