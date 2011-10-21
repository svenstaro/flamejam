from datetime import datetime, timedelta
from hashlib import sha512
from random import randint
import random

from flask import session, redirect, url_for, escape, request, \
        render_template, flash, abort
from flaskext.mail import Message
from flamejam import app

from flamejam.models import *
from flamejam.forms import *
from flamejam.login import *

@app.route('/')
def index():
    jams = Jam.query.all()
    active_count = 0
    inactive_count = 0
    for jam in jams:
        if jam.getStatus().code == 4:
            inactive_count += 1
        else:
            active_count += 1
    return render_template('index.html', jams = jams, active_count = active_count, inactive_count = inactive_count)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if get_current_user():
        flash("You are already logged in.")
        return redirect(url_for("index"))

    next = request.args.get("next","")
    if next:
        # remember where we wanted to go
        session["next"] = next

    error = None
    form = ParticipantLogin()
    if form.validate_on_submit():
        username = form.username.data
        password = sha512((form.password.data+app.config['SECRET_KEY']).encode('utf-8')).hexdigest()
        participant = Participant.query.filter_by(username=username).first()
        if not login_as(participant):
            # not verified
            return redirect(url_for("verify", username=username))
        elif "next" in session:
            # no redirect where we wanted to go
            flash('You were logged in and redirected.')
            return redirect(session.pop("next"))
        else:
            flash('You were logged in.')
            return redirect(url_for('index'))
    return render_template('login.html', form=form, error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if get_current_user():
        flash("You are already logged in.")
        return redirect(url_for("index"))

    error = None
    form = ParticipantRegistration()
    if form.validate_on_submit():
        username = form.username.data.strip()
        password = form.password.data
        email = form.email.data
        receive_emails = form.receive_emails.data
        new_participant = Participant(username,
                password,
                email,
                False, # no admin
                False,  # is verified
                receive_emails)
        
        db.session.add(new_participant)
        db.session.commit()

        msg = Message("Welcome to Bacon Game Jam, " + username, 
            recipients=[email],
            sender=("bgj","noreply@bacongamejam.org"))

        msg.body = "Click the following link to verify your registration " + \
            "http://bacongamejam.org/verify/" + username + "/" + \
            new_participant.getVerificationHash()
        mail.send(msg)

        flash("Your account has been created, confirm your email to verify.")
        return redirect(url_for('verify_status', username=username))

    return render_template('register.html', form=form, error=error)

@app.route('/verify_status/', methods=["GET"])
def verify_status():

    username = request.args.get('username', '')
    submitted = request.args.get('submitted', None)
    participant = Participant.query.filter_by(username = username).first_or_404()

    if participant.is_verified:
        flash("%s's account is already validated." % participant.username.capitalize())
        return redirect(url_for('index'))

    return render_template('verify_status.html', submitted=submitted, username=username)

@app.route('/verify/<username>/<verification>', methods=["GET"])
def verify(username, verification):

    participant = Participant.query.filter_by(username = username).first_or_404()

    if participant.is_verified:
        flash("%s's account is already validated." % participant_to_verify.username.capitalize())
        return redirect(url_for('index'))
    
    # verification success
    if verification == participant.getVerificationHash():
        participant.is_verified = True
        db.session.commit()

        flash("Your email has been confirmed, you may now login")
        return redirect(url_for('login'))

    # verification failure
    else:
        return redirect(url_for('verify_status', username=username, submitted=True))

@app.route('/logout')
def logout():
    require_login()

    logout_now()
    flash('You were logged out')
    return redirect(url_for('index'))

@app.route('/new_jam', methods=("GET", "POST"))
def new_jam():
    require_admin()

    form = NewJam()
    if form.validate_on_submit():
        title = form.title.data
        new_slug = get_slug(title)
        if Jam.query.filter_by(slug = new_slug).first():
            flash('A jam with a similar title already exists.')
        else:
            start_time = form.start_time.data
            new_jam = Jam(title, get_current_user(), start_time)
            new_jam.theme = form.theme.data
            new_jam.end_time = start_time + timedelta(hours = form.duration.data)
            db.session.add(new_jam)
            db.session.commit()
            flash('New jam added.')

            # Send out mails to all interested users.
            with mail.connect() as conn:
                participants = Participant.query.filter_by(receive_emails=True).all()
                for participant in participants:
                    msg = Message("BaconGameJam: Jam \"%s\" announced" % title)
                    msg.html = render_template("emails/jam_announced.html", jam = new_jam, recipient = participant)
                    msg.recipients = [participant.email]
                    conn.send(msg)
                flash("Email notifications have been sent.")

            #return render_template("emails/jam_announced.html", jam = new_jam, recipient = get_current_user())
            return redirect(new_jam.url())
    return render_template('new_jam.html', form = form)

@app.route('/jams/')
def jams():
    return render_template("search.html", jams = Jam.query.all())

@app.route('/jams/<jam_slug>/', methods=("GET", "POST"))
def show_jam(jam_slug):
    jam = Jam.query.filter_by(slug = jam_slug).first_or_404()
    return render_template('show_jam.html', jam = jam)

@app.route('/jams/<jam_slug>/edit', methods=("GET", "POST"))
def edit_jam(jam_slug):
    require_admin()
    jam = Jam.query.filter_by(slug = jam_slug).first_or_404()

    if not 0 <= jam.getStatus().code <= 1:
        # editing only during the jam and before
        flash("The jam is over, you cannot edit it anymore.")
        return redirect(jam.url())

    form = EditJam()
    if form.validate_on_submit():
        # remember what has changed
        changes = {}
        changes["theme"] = [jam.theme != form.theme.data, jam.theme]
        changes["title"] = [jam.title != form.title.data, jam.title]
        changes["start_time"] = [jam.start_time != form.start_time.data, jam.start_time]

        title_changed = jam.title != form.title.data
        start_time_changed = jam.start_time != form.start_time.data

        # change the options
        jam.theme = form.theme.data
        jam.title = form.title.data
        jam.start_time = form.start_time.data
        db.session.commit()

        changed = (changes["theme"][0] or
            changes["title"][0] or
            changes["start_time"][0])

        if not changed:
            flash("Nothing has changed. Keep moving!")
        else:
            # inform users about change
            if form.email.data:
                with mail.connect() as conn:
                    participants = Participant.query.filter_by(receive_emails=True).all()
                    for participant in participants:
                        msg = Message("BaconGameJam: Jam \"%s\" changed" % changes["title"][1])
                        msg.html = render_template("emails/jam_changed.html", jam = jam, changes = changes, recipient = participant)
                        msg.recipients = [participant.email]
                        conn.send(msg)
                    flash("Email notifications have been sent.")

            flash("The jam has been changed.")
        return redirect(jam.url())

    elif request.method != "POST":
        form.title.data = jam.title
        form.theme.data = jam.theme
        form.start_time.data = jam.start_time

    return render_template('edit_jam.html', jam = jam, form = form)

@app.route('/jams/<jam_slug>/countdown', methods=("GET", "POST"))
def countdown(jam_slug):
    jam = Jam.query.filter_by(slug = jam_slug).first_or_404()
    return render_template('countdown.html', jam = jam)

@app.route('/jams/<jam_slug>/new_entry', methods=("GET", "POST"))
def new_entry(jam_slug):
    require_login()

    error = None
    form = SubmitEditEntry()
    jam = Jam.query.filter_by(slug = jam_slug).first_or_404()

    if not 1 <= jam.getStatus().code <= 2:
        # new entries only during the jam and the packaging phase
        flash("New entries are not allowed at this time.")
        return redirect(jam.url())

    # check if the user has already an entry in this jam
    for entry in jam.entries:
        if entry.participant == get_current_user():
            flash("You already have an entry for this jam. Look here!")
            return redirect(entry.url())
        elif get_current_user() in entry.team:
            flash("You are part of this team! Leave the team to create your own entry.")
            return redirect(entry.url())

    if form.validate_on_submit():
        title = form.title.data
        new_slug = models.get_slug(title)
        description = form.description.data
        if Entry.query.filter_by(slug = new_slug, jam = jam).first():
            error = 'An entry with a similar name already exists for this jam'
        else:
            new_entry = Entry(title, description, jam, get_current_user())
            db.session.add(new_entry)
            db.session.commit()
            flash('Entry submitted')
            return redirect(new_entry.url())
    return render_template('new_entry.html', jam = jam, form = form, error = error)

@app.route('/jams/<jam_slug>/rate')
@app.route('/jams/<jam_slug>/rate/<action>', methods=("GET", "POST"))
def rate_entries(jam_slug, action = None):
    require_login()

    jam = Jam.query.filter_by(slug = jam_slug).first_or_404()

    # Check whether jam is in rating period
    if jam.getStatus().code != 3:
        flash("Rating for this jam is closed.")
        return redirect(jam.url())

    error = None
    skip_form = SkipRating()
    rate_form = RateEntry()
    # TODO: Filter for jams that match the the criteria to enable rating
    # (needs to happen during rating period only)
    # TODO: Keep track of who already rated

    if action == "submit_rating" and rate_form.validate_on_submit():
        entry_id = rate_form.entry_id.data
        entry = Entry.query.filter_by(id = entry_id).first_or_404()

        # check if user can rate this entry
        if not get_current_user().canRate(entry):
            flash("You cannot rate your own entry.")
            return redirect(url_for("rate_entries", jam_slug = jam.slug))

        # remove previous rating, if any
        edited = False
        if get_current_user().ratedEntry(entry):
            old_entry = Rating.query.filter_by(entry_id = entry.id, participant_id = get_current_user().id).first_or_404()
            db.session.delete(old_entry)
            edited = True

        # remove skip mark, if any
        if get_current_user().skippedEntry(entry):
            rating_skip = RatingSkip.query.filter_by(entry_id = entry.id, participant_id = get_current_user().id).first_or_404()
            db.session.delete(rating_skip)

        # read data from form
        score_gameplay = rate_form.score_gameplay.data
        score_graphics = rate_form.score_graphics.data
        score_audio = rate_form.score_audio.data
        score_innovation = rate_form.score_innovation.data
        score_story = rate_form.score_story.data
        score_technical = rate_form.score_technical.data
        score_controls = rate_form.score_controls.data
        score_overall = rate_form.score_overall.data
        note = rate_form.note.data

        # create new rating
        new_rating = Rating(score_gameplay, score_graphics, score_audio, score_innovation,
                score_story, score_technical, score_controls, score_overall,
                note, entry, get_current_user())
        db.session.add(new_rating)
        db.session.commit()
        flash('You rated for %s' % entry.title)
        return redirect(url_for('rate_entries', jam_slug = jam.slug))

    elif action == "skip_rating" and skip_form.validate_on_submit():
        entry_id = rate_form.entry_id.data
        entry = Entry.query.filter_by(id = entry_id).first_or_404()

        # error if you have already rated
        if get_current_user().ratedEntry(entry):
            flash("You already rated for %s." % entry.title)
            return redirect(url_for("rate_entries", jam_slug = jam.slug))

        # remove skip mark, if any
        if get_current_user().skippedEntry(entry):
            rating_skip = RatingSkip.query.filter_by(entry_id = entry.id, participant_id = get_current_user().id).first_or_404()
            db.session.delete(rating_skip)

        # read data from form
        reason = skip_form.reason.data
        skip = RatingSkip(get_current_user(), entry, reason)
        db.session.add(skip)
        db.session.commit()
        flash('You skipped rating for %s' % entry.title)
        return redirect(url_for('rate_entries', jam_slug = jam.slug))

    # Find all entries from this jam, including their rating count, ordered
    # by rating count ascending. Steps:
    # - select entries
    # - also select their rating count and label this "rcount" for later sorting
    # - outer join with rating to get count even if there are no ratings
    # - group by entry to count ratings PER ENTRY
    # - order by rating count, ascending (default)

    pairs = db.session.query(
            Entry,
            db.func.count(Rating.id).label("rcount"))\
        .filter_by(jam_id = jam.id)\
        .outerjoin(Rating)\
        .group_by(Entry.id)\
        .order_by("rcount")\
        .all()

    # Sort them into skipped, rated and "new" entries (that's what we
    # call them for now)
    rated_entries = []
    skipped_entries = []
    new_entries = []
    my_entries = 0

    for pair in pairs:
        # ignore entries by the user
        if get_current_user() == pair[0].participant or get_current_user() in pair[0].team:
            my_entries = my_entries + 1
            continue

        if get_current_user().ratedEntry(pair[0]):
            rated_entries.append(pair)
        elif get_current_user().skippedEntry(pair[0]):
            skipped_entries.append(pair)
        else:
            new_entries.append(pair)

    # Luckily, the lists are still sorted

    entry = None
    is_skipped_entry = False
    if new_entries:
        # We got at least 1 new entry. Take the first one.
        # TODO: Choose a random entry if the lowest numbers of ratings is not
        # unique so that people rating at the same time might get different entries
        # to rate on
        entry = new_entries[0][0]
    elif skipped_entries:
        # We don't have any new entries left, but some skipped ones. Take the first one.
        entry = random.choice(skipped_entries)[0]
        is_skipped_entry = True

    if entry:
        # We are going to display the form. Set the entry id into the hidden fields.
        rate_form.entry_id.data = entry.id
        skip_form.entry_id.data = entry.id
        return render_template("rate_entries.html", jam = jam, error = error,
            entry = entry, is_skipped_entry = is_skipped_entry, rate_form = rate_form,
            skip_form = skip_form, my_entries = my_entries)
    else:
        # We have nothing left to vote on
        flash("You have no entries left to vote on. Thanks for participating.")
        return redirect(jam.url())

@app.route('/jams/<jam_slug>/<entry_slug>/')
@app.route('/jams/<jam_slug>/<entry_slug>/<action>', methods=("GET", "POST"))
def show_entry(jam_slug, entry_slug, action=None):
    comment_form = WriteComment()
    jam = Jam.query.filter_by(slug = jam_slug).first_or_404()
    entry = Entry.query.filter_by(slug = entry_slug).filter_by(jam = jam).first_or_404()

    if action == "new_comment" and comment_form.validate_on_submit():
        require_login()
        text = comment_form.text.data
        new_comment = Comment(text, entry, get_current_user())
        db.session.add(new_comment)
        db.session.commit()
        flash('Comment added')
        return redirect(url_for('show_entry', jam_slug = jam_slug, entry_slug = entry_slug))

    if action == "edit":
        require_user(entry.participant)
        error = ""
        edit_form = SubmitEditEntry()
        if edit_form.validate_on_submit():
            title = edit_form.title.data
            new_slug = models.get_slug(title)
            description = edit_form.description.data
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
        require_user(entry.participant)

        screen_form = EntryAddScreenshot()
        if screen_form.validate_on_submit():
            s = EntryScreenshot(screen_form.url.data, screen_form.caption.data, entry)
            db.session.add(s)
            db.session.commit()
            flash("Your screenshot has been added.")
            return redirect(entry.url())

        return render_template("add_screenshot.html", entry = entry, form = screen_form)

    if action == "add_package":
        require_user(entry.participant)

        package_form = EntryAddPackage()
        if package_form.validate_on_submit():
            s = EntryPackage(entry, package_form.url.data, package_form.type.data)
            db.session.add(s)
            db.session.commit()
            flash("Your package has been added.")
            return redirect(entry.url())

        return render_template("add_package.html", entry = entry, form = package_form)

    if action == "add_team_member":
        require_user(entry.participant)

        team_form = EntryAddTeamMember()
        if team_form.validate_on_submit():
            member = Participant.query.filter_by(username = team_form.username.data).first_or_404()
            if member == get_current_user():
                flash("You cannot add yourself to the team.")
            elif not member:
                flash("That username does not exist.")
            elif member in entry.team:
                flash("That participant is already in the team.")
            elif member.getEntryInJam(entry.jam):
                flash("That participant has an entry for this jam. Look here!")
                return redirect(member.getEntryInJam(entry.jam).url())
            elif member.getTeamEntryInJam(entry.jam):
                flash("That participant is already part of a team for this jam. Look here!")
                return redirect(member.getTeamEntryInJam(entry.jam).url())
            else:
                entry.team.append(member)
                db.session.commit()
                flash("%s has been added to the team." % member.username)
                return redirect(entry.url())

        return render_template("add_team_member.html", entry = entry, form = team_form)

    if action == "remove_screenshot":
        require_user(entry.participant)

        remove_id = request.args.get("remove_id", "")
        s = EntryScreenshot.query.filter_by(entry_id = entry.id, id = remove_id).first_or_404()
        db.session.delete(s)
        db.session.commit()
        flash("The screenshot has been removed.")
        return redirect(entry.url())

    if action == "remove_package":
        require_user(entry.participant)

        remove_id = request.args.get("remove_id", "")
        s = EntryPackage.query.filter_by(entry_id = entry.id, id = remove_id).first_or_404()
        db.session.delete(s)
        db.session.commit()
        flash("The package has been removed.")
        return redirect(entry.url())

    if action == "remove_team_member":
        require_user(entry.participant)

        remove_id = request.args.get("remove_id", "0")
        member = Participant.query.get(remove_id)
        db.session.commit()
        entry.team.remove(member)
        db.session.commit()
        flash("%s has been removed from the team." % member.username)
        return redirect(entry.url())

    if action == "quit":
        require_user(list(entry.team))
        entry.team.remove(get_current_user())
        db.session.commit()
        flash("You have been removed from the team.")
        return redirect(entry.url())

    return render_template('show_entry.html', entry=entry, form = comment_form)

@app.route('/profile')
def profile():
    return redirect(get_current_user().url());

@app.route('/participants/<username>/')
@app.route('/users/<username>/')
def show_participant(username):
    participant = Participant.query.filter_by(username = username).first_or_404()
    return render_template('show_participant.html', participant = participant)

@app.route('/profile/disable_emails')
def disable_emails():
    require_login()
    user = get_current_user()
    user.receive_emails = False
    db.session.commit()
    flash("Your email notifications have been disabled.")
    return redirect(user.url())

@app.route('/profile/enable_emails')
def enable_emails():
    require_login()
    user = get_current_user()
    user.receive_emails = True
    db.session.commit()
    flash("Your email notifications have been enabled.")
    return redirect(user.url())

@app.route("/search")
def search():
    q = request.args.get("q", "")
    if not q:
        return redirect(url_for("index"))

    jams = Jam.query.filter(db.or_(
        Jam.title.like("%"+q+"%"))).all()

    entries = Entry.query.filter(db.or_(
        Entry.description.like("%"+q+"%"),
        Entry.title.like("%"+q+"%"))).all()

    participants = Participant.query.filter(
        Participant.username.like("%"+q+"%")).all()

    j = len(jams)
    e = len(entries)
    p = len(participants)

    if j == 1 and e == 0 and p == 0:
        return redirect(jams[0].url())
    elif j == 0 and e == 1 and p == 0:
        return redirect(entries[0].url())
    elif j == 0 and e == 0 and p == 1:
        return redirect(participants[0].url())

    return render_template("search.html", q = q, jams = jams, entries = entries, participants = participants)

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/rules')
@app.route('/rulez')
def rules():
    return render_template('rules.html')

@app.route('/stats')
@app.route('/statistics')
def statistics():
    # collect all the data

    stats = {}

    stats["total_jams"] = db.session.query(db.func.count(Jam.id)).first()[0];
    stats["total_participants"] = db.session.query(db.func.count(Participant.id)).first()[0];

    all_jam_participants = 0
    most_participants_per_jam = 0
    most_participants_jam = None
    most_entries_per_jam = 0
    most_entries_jam = None
    biggest_team_size = 0
    biggest_team_entry = None

    for jam in Jam.query.all():
        participants = 0
        for entry in jam.entries:
            teamsize = len(entry.team) + 1 # for the author
            participants += teamsize

            if teamsize > biggest_team_size:
                biggest_team_size = teamsize
                biggest_team_entry = entry

        if participants > most_participants_per_jam:
            most_participants_per_jam = participants
            most_participants_jam = jam

        entries = len(jam.entries.all())
        if entries > most_entries_per_jam:
            most_entries_per_jam = entries
            most_entries_jam = jam

        all_jam_participants += participants

    best_entries = Entry.query.all()
    best_entries.sort(cmp = entryCompare)
    stats["best_entries"] = best_entries[:3]

    participant_most_entries = Participant.query.all()
    participant_most_entries.sort(cmp = participantTotalEntryCompare)
    stats["participant_most_entries"] = participant_most_entries[:3]

    if stats["total_jams"]: # against division by zero
        stats["average_participants"] = all_jam_participants * 1.0 / stats["total_jams"];
    else:
        stats["average_participants"] = 0
    stats["most_participants_per_jam"] = most_participants_per_jam
    stats["most_participants_jam"] = most_participants_jam

    stats["total_entries"] = db.session.query(db.func.count(Entry.id)).first()[0];
    if stats["total_jams"]: # against division by zero
        stats["average_entries"] = stats["total_entries"] * 1.0 / stats["total_jams"]
    else:
        stats["average_entries"] = 0
    stats["most_entries_per_jam"] = most_entries_per_jam
    stats["most_entries_jam"] = most_entries_jam

    if stats["average_entries"]: # against division by zero
        stats["average_team_size"] = stats["average_participants"] * 1.0 / stats["average_entries"]
    else:
        stats["average_team_size"] = 0
    stats["biggest_team_size"] = biggest_team_size
    stats["biggest_team_entry"] = biggest_team_entry


    #Best rated entries
    #Participant with most entries

    return render_template('statistics.html', stats = stats)

@app.route('/announcements')
def announcements():
    announcements = Announcement.query.order_by(Announcement.posted.desc())
    return render_template('announcements.html', announcements = announcements)

@app.route('/faq')
@app.route('/faq/<page>')
def faq(page = ""):
    if page.lower() == "packaging":
        return render_template('faq_packaging.html')
    return render_template('faq.html')

@app.route('/links')
def links():
    return render_template('links.html')

@app.route('/subreddit')
def subreddit():
    return redirect("http://www.reddit.com/r/bacongamejam")

@app.errorhandler(404)
@app.errorhandler(403)
@app.errorhandler(500)
def error(error):
    return render_template("error.html", error = error), error.code

@app.errorhandler(flamejam.login.LoginRequired)
def login_required(exception):
    flash(exception.message)
    return redirect(url_for('login', next = exception.next))
