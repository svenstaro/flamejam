from flaskext.wtf import Form, TextField, TextAreaField, PasswordField,\
        DateTimeField
from flaskext.wtf import Required, Length, Optional, NumberRange, Email
from flaskext.wtf.html5 import IntegerField, EmailField

from flamejam import app

class ParticipantLogin(Form):
    username = TextField("Username", validators=[Required(), Length(max=80)])
    password = PasswordField("Password", validators=[Required()])

class ParticipantRegistration(Form):
    username = TextField("Username", validators=[Required(), Length(max=80)])
    password = PasswordField("Password", validators=[Required(), Length(min=8)])
    # Implement a second password field for verification here
    email = EmailField("Email", validators=[Required(), Email(), Length(max=256)])
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

class RateEntry(Form):
    score_graphics = IntegerField("Graphics rating (1 - worst to 10 - best)", validators=[Required(), NumberRange(min=1, max=10)])
    score_audio = IntegerField("Audio rating (1 - worst to 10 - best)", validators=[Required(), NumberRange(min=1, max=10)])
    score_innovation = IntegerField("Innovation rating (1 - worst to 10 - best)", validators=[Required(), NumberRange(min=1, max=10)])
    score_humor = IntegerField("Humor rating (1 - worst to 10 - best)", validators=[Required(), NumberRange(min=1, max=10)])
    score_fun = IntegerField("Fun rating (1 - worst to 10 - best)", validators=[Required(), NumberRange(min=1, max=10)])
    score_overall = IntegerField("Overall rating (1 - worst to 10 - best)", validators=[Required(), NumberRange(min=1, max=10)])
    note = TextAreaField("Additional notes", validators=[Optional()])

class WriteComment(Form):
    text = TextAreaField("Comment", validators=[Required(), Length(max=65535)])
