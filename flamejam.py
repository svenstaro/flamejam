from flask import Flask, session, redirect, url_for, escape, request, \
        render_template, flash

from flaskext.sqlalchemy import SQLAlchemy

from flaskext.wtf import Form, TextField, TextAreaField, DateTimeField,\
        RecaptchaField, FileField, PasswordField, Required, Length, Email,\
        NumberRange, Optional
from flaskext.wtf.html5 import IntegerField, EmailField

from datetime import datetime, timedelta
from hashlib import sha512

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flamejam.db'
app.config['SQLALCHEMY_ECHO'] = True
app.config['SECRET_KEY'] = 'lolsecret'
db = SQLAlchemy(app)

class Participant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(128))
    email = db.Column(db.String(256), unique=True)
    is_admin = db.Column(db.Boolean)
    is_verified = db.Column(db.Boolean)
    registered = db.Column(db.DateTime)
    entries = db.relationship('Entry', backref='participant', lazy='dynamic')
    ratings = db.relationship('Rating', backref='participant', lazy='dynamic')
    comments = db.relationship('Comment', backref='participant', lazy='dynamic')

    def __init__(self, username, password, email, is_admin=False,
            is_verified=False):
        self.username = username
        self.password = sha512(password).hexdigest()
        self.email = email
        self.is_admin = is_admin
        self.is_verified = is_verified
        self.registered = datetime.utcnow()

    def __repr__(self):
        return '<User %r>' % self.username

class Jam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    short_name = db.Column(db.String(16), unique=True)
    long_name = db.Column(db.String(128), unique=True)
    announced = db.Column(db.DateTime) # Date on which the jam was announced
    start_time = db.Column(db.DateTime) # The jam starts at this moment
    end_time = db.Column(db.DateTime) # The jamming phase ends at this moment
    packaging_deadline = db.Column(db.DateTime) # Packaging ends at this moment
    voting_end = db.Column(db.DateTime) # Voting period ends and jam is over
    entries = db.relationship('Entry', backref='jam', lazy='dynamic')

    def __init__(self, short_name, long_name, start_time, end_time=None,
            packaging_deadline=None, voting_end=None):
        self.short_name = short_name
        self.long_name = long_name
        self.start_time = start_time

        if end_time is None:
            self.end_time = start_time + timedelta(days=2)
        else:
            self.end_time = end_time

        if packaging_deadline is None:
            self.packaging_deadline = start_time + timedelta(days=3)
        else:
            self.packaging_deadline = packaging_deadline

        if voting_end is None:
            self.voting_end = start_time + timedelta(days=7)
        else:
            self.voting_end = voting_end

        self.announced = datetime.utcnow()

    def __repr__(self):
        return '<Jam %r>' % self.short_name

class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True)
    description = db.Column(db.Text)
    posted = db.Column(db.DateTime)
    jam_id = db.Column(db.Integer, db.ForeignKey('jam.id'))
    participant_id = db.Column(db.Integer, db.ForeignKey('participant.id'))
    ratings = db.relationship('Rating', backref='entry', lazy='dynamic')
    comments = db.relationship('Comment', backref='entry', lazy='dynamic')

    def __init__(self, name, description, jam, participant):
        self.name = name
        self.description = description
        self.jam = jam
        self.participant = participant
        self.posted = datetime.utcnow()

    def __repr__(self):
        return '<Entry %r>' % self.name

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    score_graphics = db.Column(db.SmallInteger)
    score_audio = db.Column(db.SmallInteger)
    score_innovation = db.Column(db.SmallInteger)
    score_humor = db.Column(db.SmallInteger)
    score_fun = db.Column(db.SmallInteger)
    score_overall = db.Column(db.SmallInteger)
    text = db.Column(db.Text)
    posted = db.Column(db.DateTime)
    entry_id = db.Column(db.Integer, db.ForeignKey('entry.id'))
    participant_id = db.Column(db.Integer, db.ForeignKey('participant.id'))

    def __init__(self, score_graphics, score_audio, score_innovation,
        score_humor, score_fun, score_overall, text, entry, participant):
        self.score_graphics = score_graphics
        self.score_audio = score_audio
        self.score_innovation = score_innovation
        self.score_humor = score_humor
        self.score_fun = score_fun
        self.score_overall = score_overall
        self.text = text
        self.entry = entry
        self.participant = participant
        self.posted = datetime.utcnow()

    def __repr__(self):
        return '<Rating %r>' % self.id

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text)
    posted = db.Column(db.DateTime)
    entry_id = db.Column(db.Integer, db.ForeignKey('entry.id'))
    participant_id = db.Column(db.Integer, db.ForeignKey('participant.id'))

    def __init__(self, text, entry, participant):
        self.text = text
        self.entry = entry
        self.participant = participant
        self.posted = datetime.utcnow()

    def __repr__(self):
        return '<Comment %r>' % self.id

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
    start_time = DateTimeField("Start time", validators=[Required()])
    # Add remaining fields

class SubmitEntry(Form):
    name = TextField("Entry name", validators=[Required(), Length(max=128)])
    description = TextAreaField("Description", validators=[Required()])

class RateEntry(Form):
    field = IntegerField("Graphics rating (1 - worst to 9 - best)",
        validators=[Required(), NumberRange(min=1, max=9)])
    score_graphics = field
    score_audio = field
    score_innovation = field
    score_humor = field
    score_fun = field
    score_overall = field
    text = TextAreaField("Additional notes", validators=[Optional])

class WriteComment(Form):
    text = TextAreaField("Comment", validators=[Required()])

@app.route('/')
def index():
    jams = Jam.query.all()
    return render_template('index.html', jams=jams,
            current_datetime=datetime.utcnow())

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    form = ParticipantLogin()
    if form.validate_on_submit():
        username = form.username.data
        password = sha512(form.password.data).hexdigest()
        participant = Participant.query.filter_by(username=username).first()
        if not participant:
            error = 'Invalid username'
        elif not participant.password == password:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            session['username'] = username
            if participant.is_admin:
                session['is_admin'] = True
            flash('You were logged in')
            return redirect(url_for('index'))
    return render_template('login.html', form=form, error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    form = ParticipantRegistration()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        participant = Participant.query.filter_by(username=username).first()
        if participant:
            error = 'Username already in use'
        else:
            new_participant = Participant(username, password, email)
            db.session.add(new_participant)
            db.session.commit()
            flash('Registration successful')
            return redirect(url_for('index'))
    return render_template('register.html', form=form, error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    session.pop('is_admin', None)
    #session.pop('is_verified', None)
    flash('You were logged out')
    return redirect(url_for('index'))

@app.route('/new_jam', methods=("GET", "POST"))
def new_jam():
    # use decorator
    #if not session['logged_in'] or not session['is_admin']:
    #    flash('Not an admin')
    #    return redirect(url_for('index'))
    return render_template('new_jam.html')

@app.route('/jams/<short_name>')
def show_jam(short_name):
    jam = Jam.query.filter_by(short_name=short_name).first_or_404()
    return render_template('show_jam.html', jam=jam)

@app.route('/entries/<name>')
def show_entry(name):
    entry = Entry.query.filter_by(name=name).first_or_404()
    return render_template('show_entry.html', entry=entry)

@app.route('/participants/<username>')
def show_participant(username):
    participant = Participant.query.filter_by(username=username).first_or_404()
    return render_template('show_participant.html', participant=participant)

@app.route('/contact')
def contact():
    return render_template('contact.html')

if __name__ == '__main__':
    app.run(debug=True)
