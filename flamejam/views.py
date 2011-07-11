from datetime import datetime, timedelta
from hashlib import sha512
from random import randint

from flask import session, redirect, url_for, escape, request, \
        render_template, flash, abort
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
        title = form.title.data
        start_time = form.start_time.data
        new_slug = get_slug(title)
        if Jam.query.filter_by(slug = new_slug).first():
            error = 'A jam with a similar title already exists.'
        else:
            current_user = Participant.query.filter_by(username = session["username"]).first_or_404()
            new_jam = Jam(title, current_user, start_time)
            db.session.add(new_jam)
            db.session.commit()
            flash('New jam added')
            return redirect(new_jam.url())
    return render_template('new_jam.html', form = form, error = error)

@app.route('/jams/<jam_slug>/', methods=("GET", "POST"))
def show_jam(jam_slug):
    jam = Jam.query.filter_by(slug = jam_slug).first_or_404()
    return render_template('show_jam.html', jam = jam)

@app.route('/jams/<jam_slug>/new_entry', methods=("GET", "POST"))
def new_entry(jam_slug):
    error = None
    form = SubmitEditEntry()
    jam = Jam.query.filter_by(slug = jam_slug).first_or_404()
    if form.validate_on_submit():
        title = form.title.data
        new_slug = models.get_slug(title)
        description = form.description.data
        participant_username = session['username']
        participant = Participant.query.filter_by(username=participant_username).first()
        if Entry.query.filter_by(slug = new_slug, jam = jam).first():
            error = 'An entry with a similar name already exists for this jam'
        else:
            new_entry = Entry(title, description, jam, participant)
            db.session.add(new_entry)
            db.session.commit()
            flash('Entry submitted')
            return redirect(new_entry.url())
    return render_template('new_entry.html', jam = jam, form = form, error = error)

@app.route('/jams/<jam_slug>/rate', methods=("GET", "POST"))
def rate_entries(jam_slug):
   jam = Jam.query.filter_by(slug = jam_slug).first_or_404()

   skip_form = SkipRating()

   return render_template("rate_entries.html", jam = jam, entry = jam.entries.first(), skip_form = skip_form)

   # # Check whether jam is in rating period
   # if not (jam.packaging_deadline < datetime.utcnow() < jam.rating_end):
   #     abort(404)

   # # Figure out next entry (that which has fewest ratings of all entries) and
   # # present it to the user who is looking for the next entry to rate.
   # entries = jam.entries
   # entries_ordered = []
   # for entry in entries:
   #     entries_ordered.append((entry.ratings.count(), entry))
   # entries_ordered.sort()

   # # Eliminate skipped entries.
   # skipped_entries_list = []
   # if "skipped" in session:
   #     skipped_entries = session["skipped"].split("|")
   #     remaining_entries = []
   #     for entry in entries_ordered:
   #         if jam.short_name+entry[1].name in skipped_entries:
   #             skipped_entries_list.append(entry)
   #         else:
   #             remaining_entries.append(entry)

   # # Add skipped entries to end of preferred entries.
   # entries_ordered = remaining_entries + skipped_entries_list
   # flash(remaining_entries)
   # flash(entries_ordered)

   # # Figure out whether the lowest count number is unique. For instance, if
   # # the 3 first items in the list are all 2, we should assign a random one of
   # # those to all new rating requests so that ratings are more evenly
   # # distributed.
   # unique_test_list = []
   # for list_item in remaining_entries:
   #     unique_test_list.append(list_item[0]) # [0] is always ratings.count().

   # # Now test how often the lowest number appears.
   # count = unique_test_list.count(unique_test_list[0])
   # flash(count)

   # # Use one of the entries with the lowest ratings counts and provide it as
   # # this request's entry to vote on.
   # entry_number = randint(0, count - 1)
   # entry = entries_ordered[entry_number][1]

   # error = None
   # form = RateEntry()
   # # TODO: Filter for jams that match the the criteria to enable rating
   # # (needs to happen during rating period only)
   # # TODO: Keep track of who already rated

   # skip = form.skip.data
   # if skip:
   #     if "skipped" in session:
   #         session["skipped"] += jam.short_name+entry.name+"|"
   #     else:
   #         session["skipped"] = jam.short_name+entry.name+"|"
   #     return redirect(url_for('rate_entries', jam_name=jam_name))

   # if form.validate_on_submit():
   #     entry_name = session["rating_next"].replace(jam_name, "")
   #     entry_query = Entry.query.filter_by(name=entry_name).first()
   #     score_graphics = form.score_graphics.data
   #     score_audio = form.score_audio.data
   #     score_innovation = form.score_innovation.data
   #     score_humor = form.score_humor.data
   #     score_fun = form.score_fun.data
   #     score_overall = form.score_overall.data
   #     note = form.note.data
   #     participant_username = session['username']
   #     participant = Participant.query.filter_by(username=participant_username).first()
   #     new_rating = Rating(score_graphics, score_audio, score_innovation,
   #             score_humor, score_fun, score_overall, note, entry_query, participant)
   #     db.session.add(new_rating)
   #     db.session.commit()
   #     flash('Rating added')
   #     return redirect(url_for('rate_entries', jam_name=jam_name))

   # # Set next vote to the session cookie because we don't trust the user.
   # session["rating_next"] = jam.short_name+"|"+entry.name

   # entry = Entry.query.filter_by(name=entry.name).first()
   # return render_template('rate_entries.html', jam=jam,
   #         form=form, error=error, skipped_entries=skipped_entries_list)

@app.route('/jams/<jam_slug>/<entry_slug>/')
@app.route('/jams/<jam_slug>/<entry_slug>/<action>', methods=("GET", "POST"))
def show_entry(jam_slug, entry_slug, action=None):
    comment_form = WriteComment()
    jam = Jam.query.filter_by(slug = jam_slug).first_or_404()
    entry = Entry.query.filter_by(slug = entry_slug).filter_by(jam = jam).first_or_404()

    # TODO: Remove this action stuff
    if action == "new_comment" and comment_form.validate_on_submit():
        text = comment_form.text.data
        participant_username = session['username']
        participant = Participant.query.filter_by(username = participant_username).first_or_404()
        new_comment = Comment(text, entry, participant)
        db.session.add(new_comment)
        db.session.commit()
        flash('Comment added')
        return redirect(url_for('show_entry', jam_slug = jam_slug,
            entry_slug = entry_slug))


    if action == "edit":
        if entry.participant.username != session["username"]:
            abort(403)

        error = ""

        edit_form = SubmitEditEntry()
        if edit_form.validate_on_submit():
            title = edit_form.title.data
            new_slug = models.get_slug(title)
            description = edit_form.description.data
            participant_username = session['username']
            participant = Participant.query.filter_by(username=participant_username).first()
            old_entry = Entry.query.filter_by(slug = new_slug, jam = jam).first()
            if old_entry and old_entry != entry:
                error = 'An entry with a similar name already exists for this jam.'
            else:
                entry.title = title
                entry.slug = new_slug
                entry.description = description
                db.session.commit()
                flash("Your changes have been saved.")
                return redirect(entry.url())
        elif request.method != "POST":
            edit_form.title.data = entry.title
            edit_form.description.data = entry.description

        return render_template('edit_entry.html', entry = entry, form = edit_form, error = error)

    if action == "add_screenshot":
        screen_form = EntryAddScreenshot()

        if screen_form.validate_on_submit():
            s = EntryScreenshot(screen_form.url.data, screen_form.caption.data, entry)
            db.session.add(s)
            db.session.commit()
            flash("Your screenshot has been added.")
            return redirect(entry.url())

        return render_template("add_screenshot.html", entry = entry, form = screen_form)

    if action == "add_package":
        package_form = EntryAddPackage()

        if package_form.validate_on_submit():
            s = EntryPackage(entry, package_form.url.data, package_form.type.data)
            db.session.add(s)
            db.session.commit()
            flash("Your package has been added.")
            return redirect(entry.url())

        return render_template("add_package.html", entry = entry, form = package_form)

    return render_template('show_entry.html', entry=entry, form = comment_form)

@app.route('/participants/<username>/')
def show_participant(username):
    participant = Participant.query.filter_by(username = username).first_or_404()
    return render_template('show_participant.html', participant = participant)

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
