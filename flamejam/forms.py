# -*- coding: utf-8 -*-

from wtforms.fields import *
from wtforms.validators import *
from wtforms.validators import ValidationError
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from flask.ext.wtf import Form, RecaptchaField
from flask.ext.wtf.file import FileField, FileAllowed, FileRequired
from flask.ext.wtf.html5 import IntegerField, EmailField, IntegerRangeField, IntegerField
import re
from flamejam import app, models, utils
from flamejam.models.rating import RATING_CATEGORIES
from sqlalchemy import func

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
        if not re.search(self.regex, field.data):
            raise ValidationError(self.message.format(self.regex))

class UsernameExists(object):
    def __call__(self, form, field):
        u = models.User.query.filter(func.lower(models.User.username) == func.lower(field.data)).first()
        if not u:
            raise ValidationError("The username does not exist.")

class EmailExists(object):
    def __call__(self, form, field):
        e = models.User.query.filter_by(email = field.data).first()
        if not e:
            raise ValidationError("That email does not exist")

class LoginValidator(object):
    def __init__(self, pw_field, message_username = "The username or password is incorrect.", message_password = "The username or password is incorrect."):
        self.pw_field = pw_field
        self.message_username = message_username
        self.message_password = message_password

    def __call__(self, form, field):
        u = models.User.query.filter(func.lower(models.User.username) == func.lower(field.data)).first()
        if not u:
            raise ValidationError(self.message_username)
        elif not utils.verify_password(u.password, form[self.pw_field].data):
            raise ValidationError(self.message_password)

class UsernameValidator(object):
    def __init__(self, message_username = "The username is incorrect."):
        self.message_username = message_username

    def __call__(self, form, field):
        u = models.User.query.filter(func.lower(models.User.username) == func.lower(field.data)).first()
        if not u:
            raise ValidationError(self.message_username)

############## FORMS ####################

class UserLogin(Form):
    username = TextField("Username", validators=[LoginValidator("password")])
    password = PasswordField("Password", validators = [])
    remember_me = BooleanField("Remember me", default = False)

class UserRegistration(Form):
    username = TextField("Username", validators=[
        Not(MatchesRegex("[^0-9a-zA-Z\-_]"), message = "Your username contains invalid characters. Only use alphanumeric characters, dashes and underscores."),
        Not(UsernameExists(), message = "That username already exists."),
        Length(min=3, max=80, message="You have to enter a username of 3 to 80 characters length.")])
    password = PasswordField("Password", validators=[Length(min=8, message = "Please enter a password of at least 8 characters.")])
    password2 = PasswordField("Password, again", validators=[EqualTo("password", "Passwords do not match.")])
    email = EmailField("Email", validators=[
            Not(EmailExists(), message = "That email address is already in use."),
            Email(message = "The email address you entered is invalid.")])
    captcha = RecaptchaField()

class ResetPassword(Form):
    username = TextField("Username", validators=[UsernameValidator()])
    captcha = RecaptchaField()

class NewPassword(Form):
    password = PasswordField("Password", validators=[Length(min=8, message = "Please enter a password of at least 8 characters.")])
    password2 = PasswordField("Password, again", validators=[EqualTo("password", "Passwords do not match.")])

class VerifyForm(Form):
    pass

class ContactUserForm(Form):
    message = TextAreaField("Message", validators=[Required()])
    captcha = RecaptchaField("Captcha")

class JamDetailsForm(Form):
    title = TextField("Title", validators=[Required(), Length(max=128)])
    theme = TextField("Theme", validators=[Length(max=128)])
    team_limit = IntegerField("Team size limit", validators=[NumberRange(min = 0)])
    start_time = DateTimeField("Start time", format="%Y-%m-%d %H:%M", validators=[Required()])

    registration_duration = IntegerField("Registration duration", validators=[Required(), NumberRange(min = 0)], default = 14 * 24)
    packaging_duration = IntegerField("Packaging duration", validators=[Required(), NumberRange(min = 0)], default = 24)
    rating_duration = IntegerField("Rating duration", validators=[Required(), NumberRange(min = 0)], default = 24 * 5)
    duration = IntegerField("Duration", validators=[Required(), NumberRange(min = 0)], default = 24 * 2)

    description = TextAreaField("Description")
    restrictions = TextAreaField("Restrictions")

class GameCreateForm(Form):
    title = TextField("Game title", validators=[Required(), Length(max=128)])

class GameEditForm(Form):
    title = TextField("Game title", validators=[Required(), Length(max=128)])
    description = TextAreaField("Description", validators=[Required()])
    technology = TextAreaField("Technlogoy used")
    help = TextAreaField("Help / Controls")

    def get(self, name):
        return getattr(self, "score_" + name + "_enabled")

# Adds fields "dynamically" (which score categories are enabled?)
for c in RATING_CATEGORIES:
    setattr(GameEditForm, "score_" + c + "_enabled", BooleanField(c.title()))

class GameAddScreenshotForm(Form):
    url = TextField("URL", validators = [Required(), URL()])
    caption = TextField("Caption", validators = [Required()])

class GameAddTeamMemberForm(Form):
    username = TextField("Username:", validators = [Required(), UsernameExists()])

from models import GamePackage

class GameAddPackageForm(Form):
    url = TextField("URL", validators = [Required(), URL()])
    type = SelectField("Type", choices = [
        ("web",          GamePackage.typeString("web")),
        ("linux",        GamePackage.typeString("linux")),
        ("linux32",      GamePackage.typeString("linux32")),
        ("linux64",      GamePackage.typeString("linux64")),
        ("windows",      GamePackage.typeString("windows")),
        ("windows64",    GamePackage.typeString("windows64")),
        ("mac",          GamePackage.typeString("mac")),
        ("source",       GamePackage.typeString("source")),
        ("git",          GamePackage.typeString("git")),
        ("svn",          GamePackage.typeString("svn")),
        ("hg",           GamePackage.typeString("hg")),
        ("combi",        GamePackage.typeString("combi")),
        ("love",         GamePackage.typeString("love")),
        ("blender",      GamePackage.typeString("blender")),
        ("unknown",      GamePackage.typeString("unknown"))])

class RateGameForm(Form):
    score = IntegerField("Overall rating", validators=[Required(), NumberRange(min=0, max=10)], default = 5)
    # score_CATEGORY = IntegerField("Category rating", validators=[Required(), NumberRange(min=0, max=10)], default = 5)
    note = TextAreaField("Additional notes", validators=[Optional()])

    def get(self, name):
        return getattr(self, "score" if name in (None, "overall") else ("score_" + name))

for x in models.rating.RATING_CATEGORIES:
    setattr(RateGameForm, "score_" + x, IntegerField(x.capitalize() + " rating",
        validators=[Required(), NumberRange(min=0, max=10)], default = 5))

class WriteComment(Form):
    text = TextAreaField("Comment", validators=[Required(), Length(max=65535)])

class TeamFinderFilter(Form):
    need_programmer = BooleanField("Programmer", default = True)
    need_gamedesigner = BooleanField("Game Designer", default = True)
    need_2dartist = BooleanField("2D Artist", default = True)
    need_3dartist = BooleanField("3D Artist", default = True)
    need_composer = BooleanField("Composer", default = True)
    need_sounddesigner = BooleanField("Sound Designer", default = True)

    show_teamed = BooleanField("people with a team")
    show_empty = BooleanField("people w/o abilities set", default = True)

    order = SelectField("Sort by", choices = [
        ("abilities", "Ability match"),
        ("username", "Username"),
        ("location", "Location")
    ], default = "abilities")

class SettingsForm(Form):
    ability_programmer = BooleanField("Programming")
    ability_gamedesigner = BooleanField("Game Design")
    ability_2dartist = BooleanField("Graphics / 2D Art")
    ability_3dartist = BooleanField("Modelling / 3D Art")
    ability_composer = BooleanField("Composing")
    ability_sounddesigner = BooleanField("Sound Design")
    abilities_extra = TextField("Detailed abilities")
    location = TextField("Location")
    real_name = TextField("Real Name")
    about = TextAreaField("About me")
    website = TextField("Website / Blog")
    avatar = TextField("Avatar URL", validators=[Optional(), URL()])

    old_password = PasswordField("Old Password", validators=[Optional()])
    new_password = PasswordField("New Password", validators=[Optional(), Length(min=8, message = "Please enter a password of at least 8 characters.")])
    new_password2 = PasswordField("New Password, again", validators=[EqualTo("new_password", "Passwords do not match.")])

    email = EmailField("Email", validators=[
        Optional(),
        Email(message = "The email address you entered is invalid.")])

    pm_mode = SelectField("Allow PM", choices = [
        ("email", "show my address"),
        ("form", "use email form"),
        ("disabled", "disable email")
    ], default = "form")

    notify_new_jam = BooleanField("when a jam is announced")
    notify_jam_start = BooleanField("when a jam I participate in starts")
    notify_jam_finish = BooleanField("when a jam I participate in finishes")
    notify_game_comment = BooleanField("when someone comments on a game of mine")
    notify_team_invitation = BooleanField("when someone invites me to a team")

    notify_newsletter = BooleanField("send me newsletters")

class ParticipateForm(Form):
    show_in_finder = BooleanField("Show me in the team finder")

class CancelParticipationForm(Form):
    confirm = BooleanField("I understand that, please cancel my participation", validators = [Required()])

class LeaveTeamForm(Form):
    confirm = BooleanField("I understand that, and want to leave the team", validators = [Required()])

class TeamSettingsForm(Form):
    name = TextField("Team Name", validators=[Required()])
    description = TextAreaField("Description")
    livestreams = TextAreaField("Livestreams")
    irc = TextField("IRC Channel")

class InviteForm(Form):
    username = TextField("Username", validators=[Required()])

class AdminWriteAnnouncement(Form):
    subject = TextField("Subject", validators=[Required()])
    message = TextAreaField("Content", validators=[Required()])

class AdminUserForm(Form):
    username = TextField("Username", validators=[
        Not(MatchesRegex("[^0-9a-zA-Z\-_]"), message = "Your username contains invalid characters. Only use alphanumeric characters, dashes and underscores."),
        Length(min=3, max=80, message="You have to enter a username of 3 to 80 characters length.")])
    avatar = TextField("Avatar URL", validators=[Optional(), URL()])
    email = EmailField("Email", validators=[
        Optional(),
        Email(message = "The email address you entered is invalid.")])
