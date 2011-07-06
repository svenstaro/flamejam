from flaskext.wtf import Form, TextField, TextAreaField, PasswordField,\
        DateTimeField, SubmitField
from flaskext.wtf import Required, Length, EqualTo, Optional, NumberRange, Email,\
        ValidationError
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

class NewJam(Form):
    short_name = TextField("Short name", validators=[Required(), Length(max=16)])
    long_name = TextField("Long name", validators=[Required(), Length(max=128)])
    start_time = DateTimeField("Start time (format: 2012-11-25 22:00)",
            format="%Y-%m-%d %H:%M", validators=[Required()])
    # Add remaining fields

class SubmitEntry(Form):
    name = TextField("Entry name", validators=[Required(), Length(max=128)])
    description = TextAreaField("Description", validators=[Required()])

    def validate_name(form, field):
        if "|" in form.name.data:
            raise ValidationError("Name can not contain '|'")

class RateEntry(Form):
    score_graphics = IntegerField("Graphics rating (1 - worst to 10 - best)", validators=[Required(), NumberRange(min=1, max=10)])
    score_audio = IntegerField("Audio rating (1 - worst to 10 - best)", validators=[Required(), NumberRange(min=1, max=10)])
    score_innovation = IntegerField("Innovation rating (1 - worst to 10 - best)", validators=[Required(), NumberRange(min=1, max=10)])
    score_humor = IntegerField("Humor rating (1 - worst to 10 - best)", validators=[Required(), NumberRange(min=1, max=10)])
    score_fun = IntegerField("Fun rating (1 - worst to 10 - best)", validators=[Required(), NumberRange(min=1, max=10)])
    score_overall = IntegerField("Overall rating (1 - worst to 10 - best)", validators=[Required(), NumberRange(min=1, max=10)])
    note = TextAreaField("Additional notes", validators=[Optional()])
    skip = SubmitField("Skip", validators=[Optional()])

class WriteComment(Form):
    text = TextAreaField("Comment", validators=[Required(), Length(max=65535)])
