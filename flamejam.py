from flask import Flask, session, redirect, url_for, escape, request, \
        render_template

from flaskext.sqlalchemy import SQLAlchemy

from datetime import datetime, timedelta
from hashlib import sha512

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flamejam.db'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)

class Participant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(128))
    email = db.Column(db.String(256), unique=True)
    registered = db.Column(db.DateTime)
    verified = db.Column(db.Boolean)
    entries = db.relationship('Entry', backref='participant', lazy='dynamic')

    def __init__(self, username, password, email):
        self.username = username
        self.password = sha512(password).hexdigest()
        self.email = email
        self.registered = datetime.utcnow()
        self.verified = False

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
    jam_id = db.Column(db.Integer, db.ForeignKey('jam.id'))
    participant_id = db.Column(db.Integer, db.ForeignKey('participant.id'))

    def __init__(self, name, description, jam, participant):
        self.name = name
        self.description = description
        self.jam = jam
        self.participant = participant

        def __repr__(self):
            return '<Entry %r>' % self.name

@app.route('/')
def index():
    jams = Jam.query.all()
    return render_template('index.html', jams=jams,
            current_datetime=datetime.utcnow())

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/new_jam')
def new_jam():
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

if __name__ == '__main__':
    app.run(debug=True)
