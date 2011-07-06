from datetime import datetime, timedelta
from hashlib import sha512

from flask import session, redirect, url_for, escape, request, \
        render_template, flash
from flamejam import app

from flamejam.models import *
from flamejam.forms import *

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
    error = None
    form = NewJam()
    # use decorator to check whether user is logged in and is admin
    #if not session['logged_in'] or not session['is_admin']:
    #    flash('Not an admin')
    #    return redirect(url_for('index'))
    if form.validate_on_submit():
        short_name = form.short_name.data
        long_name = form.long_name.data
        start_time = form.start_time.data
        if Jam.query.filter_by(short_name=short_name).first():
            error = 'A jam with this Short name already exists'
        elif Jam.query.filter_by(long_name=long_name).first():
            error = 'A jam with this Long name already exists'
        else:
            new_jam = Jam(short_name, long_name, start_time)
            db.session.add(new_jam)
            db.session.commit()
            flash('New jam added')
            return redirect(url_for('index'))
    return render_template('new_jam.html', form=form, error=error)

@app.route('/jams/<jam_name>/', methods=("GET", "POST"))
def show_jam(jam_name):
    jam = Jam.query.filter_by(short_name=jam_name).first_or_404()
    return render_template('show_jam.html', jam=jam)

@app.route('/jams/<jam_name>/new_entry', methods=("GET", "POST"))
def new_entry(jam_name):
    error = None
    form = SubmitEntry()
    jam = Jam.query.filter_by(short_name=jam_name).first_or_404()
    if form.validate_on_submit():
        name = form.name.data
        description = form.description.data
        participant_username = session['username']
        participant = Participant.query.filter_by(username=participant_username).first()
        if Entry.query.filter_by(name=name).filter_by(jam=jam).first():
            error = 'An entry with this name already exists for this jam'
        else:
            new_entry = Entry(name, description, jam, participant)
            db.session.add(new_entry)
            db.session.commit()
            flash('Entry submitted')
            return redirect(url_for('show_entry', jam_name=jam_name, entry_name=name))
    return render_template('new_entry.html', jam=jam, form=form, error=error)

@app.route('/jams/<jam_name>/<entry_name>/')
@app.route('/jams/<jam_name>/<entry_name>/<action>', methods=("GET", "POST"))
def show_entry(jam_name, entry_name, action=None):
    form_rating = RateEntry()
    form_comment = WriteComment()
    jam = Jam.query.filter_by(short_name=jam_name).first_or_404()
    entry = Entry.query.filter_by(name=entry_name).filter_by(jam=jam).first_or_404()

    if action == "new_rating" and form_rating.validate_on_submit():
        score_graphics = form_rating.score_graphics.data
        score_audio = form_rating.score_audio.data
        score_innovation = form_rating.score_innovation.data
        score_humor = form_rating.score_humor.data
        score_fun = form_rating.score_fun.data
        score_overall = form_rating.score_overall.data
        note = form_rating.note.data
        participant_username = session['username']
        participant = Participant.query.filter_by(username=participant_username).first()
        new_rating = Rating(score_graphics, score_audio, score_innovation,
                score_humor, score_fun, score_overall, note, entry, participant)
        db.session.add(new_rating)
        db.session.commit()
        flash('Rating added')
        return redirect(url_for('show_entry', jam_name=jam_name,
            entry_name=entry_name))

    if action == "new_comment" and form_comment.validate_on_submit():
        text = form_comment.text.data
        participant_username = session['username']
        participant = Participant.query.filter_by(username=participant_username).first()
        new_comment = Comment(text, entry, participant)
        db.session.add(new_comment)
        db.session.commit()
        flash('Comment added')
        return redirect(url_for('show_entry', jam_name=jam_name,
            entry_name=entry_name))

    return render_template('show_entry.html', entry=entry,
            form_rating=form_rating, form_comment=form_comment)

@app.route('/participants/<username>/')
def show_participant(username):
    participant = Participant.query.filter_by(username=username).first_or_404()
    return render_template('show_participant.html', participant=participant)

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/rules')
@app.route('/rulez')
def rules():
    return render_template('rules.html')
    
@app.route('/announcements')
def announcements():
    announcements = Announcement.query.order_by(Announcement.posted.desc())
    return render_template('announcements.html', announcements = announcements)
