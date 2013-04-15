from datetime import datetime, timedelta
from hashlib import sha512
from random import randint
import random
import smtplib
import sys

from flask import session, redirect, url_for, escape, request, \
        render_template, flash, abort
from flamejam import app

from flamejam.menu import *
from flamejam.models import *
from flamejam.forms import *
from flamejam.login import *
from flamejam.mail import *

@app.route('/')
@path("Index")
def index():
    for jam in Jam.query.all():
        if jam.getStatus().code == JamStatusCode.RUNNING:
            return redirect(jam.url())
    return redirect(url_for("home"))

@app.context_processor
def inject():
    jams = Jam.query.all()
    active_count = 0
    inactive_count = 0
    for jam in jams:
        if jam.getStatus().code == JamStatusCode.FINISHED:
            inactive_count += 1
        else:
            active_count += 1
    return dict(all_jams = jams, active_jams = active_count, inactive_jams = inactive_count)


@app.route("/home")
@path("Home")
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
@path("Login")
def login():
    if get_current_user():
        flash("You are already logged in.", "info")
        return redirect(url_for("index"))

    next = request.args.get("next","")
    if next:
        # remember where we wanted to go
        session["next"] = next

    login_form = UserLogin()
    register_form = UserRegistration()

    if login_form.validate_on_submit():
        username = login_form.username.data
        password = sha512((login_form.password.data+app.config['SECRET_KEY']).encode('utf-8')).hexdigest()
        user = User.query.filter_by(username=username).first()
        if not login_as(user):
            return redirect(url_for("verify_status", username=username))
        elif "next" in session:
            flash("You were logged in and redirected.", "success")
            return redirect(session.pop("next"))
        else:
            flash("You were logged in.", "success")
            return redirect(url_for('index'))
    elif register_form.validate_on_submit():
        username = register_form.username.data.strip()
        password = register_form.password.data
        email = register_form.email.data
        new_user = User(username,
                password,
                email,
                False, # no admin
                False  # is verified
                )

        m = Mail("Welcome to Bacon Game Jam, " + username)
        m.addRecipient(new_user)
        m.render("emails/account/verification.html", recipient = new_user)
        m.send()

        db.session.add(new_user)
        db.session.commit()

        flash("Your account has been created, confirm your email to verify.", "success")
        return redirect(url_for('verify_status', username = username))
    return render_template('account/login.html', login_form = login_form, register_form = register_form)

@app.route('/reset', methods=['GET', 'POST'])
@path("Reset")
def reset_request():
    if get_current_user():
        flash("You are already logged in.", "info")
        return redirect(url_for("index"))
    error = None
    form = ResetPassword()
    if form.validate_on_submit():
        # thanks to the UsernameValidator we cam assume the username exists
        user = User.query.filter_by(username=form.username.data).first()
        user.token = randint(0, sys.maxint)
        db.session.commit()

        m = Mail("Reset your BGJ-Password")
        m.addRecipient(user)
        m.render("emails/account/reset_password.html", recipient = user)
        m.send()

        flash("Your password has been reset, check your email.", "success")
    return render_template('reset_request.html', form=form, error=error)

@app.route('/reset/<username>/<token>', methods=['GET', 'POST'])
@path("Reset")
def reset_verify(username, token):
    user = user.query.filter_by(username=username).first_or_404()
    if user.token == None:
        flash("%s's account has not requested a password reset." % user.username.capitalize(), "error")
        return redirect(url_for('index'))
    if user.getResetToken() != token:
        flash("This does not seem to be a valid reset link, if you reset your account multiple times make sure you are using the link in the last email you received!", "error")
        return redirect(url_for('index'))
    form = NewPassword()
    error = None
    if form.validate_on_submit():
        # null the reset token
        user.token = None
        # set the new password
        user.password = sha512((form.password.data+app.config['SECRET_KEY']).encode('utf-8')).hexdigest()
        db.session.commit()
        flash("Your password was updated and you can login with it now.", "success")
        return redirect(url_for('login'))
    return render_template('reset_newpassword.html', user = user, form = form, error = error)


@app.route('/verify/', methods=["POST", "GET"])
@path("Verify")
def verify_send():
    if request.method == 'GET':
        return redirect(url_for('index'))

    username = request.form.get('username', "")
    user = User.query.filter_by(username = username).first_or_404()

    if user.is_verified:
        flash("%s's account is already validated." % user.username.capitalize(), "info")
        return redirect(url_for('index'))


    m = Mail("Welcome to Bacon Game Jam, " + username)
    m.render("emails/account/verification.html", recipient = user)
    m.addRecipientEmail(user.new_email)
    m.send()

    flash("Verification has been resent, check your email", "success")
    return redirect(url_for('verify_status', username=username))

@app.route('/verify/<username>', methods=["GET"])
@path("Verify")
def verify_status(username):
    submitted = request.args.get('submitted', None)
    user = User.query.filter_by(username = username).first_or_404()

    if user.is_verified:
        flash("%s's account is already validated." % user.username.capitalize(), "info")
        return redirect(url_for('index'))

    return render_template('misc/verify_status.html', submitted=submitted, username=username)

@app.route('/verify/<username>/<verification>', methods=["GET"])
@path("Verify")
def verify(username, verification):

    user = User.query.filter_by(username = username).first_or_404()

    if user.is_verified:
        flash("%s's account is already validated." % user.username.capitalize(), "success")
        return redirect(url_for('index'))

    # verification success
    if verification == user.getVerificationHash():
        user.is_verified = True
        user.email = user.new_email
        db.session.commit()

        flash("Your email has been confirmed, you may now login")
        return redirect(url_for('login'))

    # verification failure
    else:
        return redirect(url_for('verify_status', username=username, submitted=True))

@app.route('/logout')
@path("Logout")
def logout():
    require_login()

    logout_now()
    flash("You were logged out.", "success")
    return redirect(url_for('index'))

@app.route("/map")
@app.route("/map/<mode>")
@app.route("/map/<mode>/<int:id>")
def map(mode = "users", id = 0):
    users = []
    extra = None
    if mode == "jam":
        extra = Jam.query.filter_by(id = id).first_or_404()
        users = extra.participants
    elif mode == "user":
        extra = User.query.filter_by(id = id).first_or_404()
        users = [extra]
    elif mode == "team":
        extra = Team.query.filter_by(id = id).first_or_404()
        users = extra.members
    else:
        mode = "users"
        users = User.query.all()

    x = 0
    for user in users:
        if user.location_coords:
            x += 1

    return render_template("misc/map.html", users = users, mode = mode, extra = extra, x = x)

@app.route('/jams/')
@path("Jams")
def jams():
    return render_template("misc/search.html", jams = Jam.query.all())

@app.route('/jams/<jam_slug>/', methods=("GET", "POST"))
@path("Jams", "Show")
def jam_info(jam_slug):
    jam = Jam.query.filter_by(slug = jam_slug).first_or_404()
    return render_template('jam/jam_info.html', jam = jam)

@app.route('/jams/<jam_slug>/register/', methods = ["POST", "GET"])
@path("Jams", "Register")
def jam_register(jam_slug):
    require_login()
    jam = Jam.query.filter_by(slug = jam_slug).first_or_404()
    user = get_current_user()

    if jam.getStatus().code > JamStatusCode.RUNNING:
        flash("You cannot register for a jam after it has finished.", "error")
        return redirect(jam.url())

    if user.getRegistration(jam):
        flash("You are already registered for this jam.", "warning")
        return redirect(jam.url())

    form = RegisterJamForm()

    if form.validate_on_submit():
        user.joinJam(jam)
        user.getRegistration(jam).show_in_finder = form.show_in_finder.data
        db.session.commit()
        flash("You are now registered for this jam.", "success")
        return redirect(jam.url())

    return render_template('jam/register.html', jam = jam, form = form)

@app.route('/jams/<jam_slug>/unregister/', methods = ["POST", "GET"])
@path("Jams", "Unregister")
def jam_unregister(jam_slug):
    require_login()
    jam = Jam.query.filter_by(slug = jam_slug).first_or_404()

    if jam.getStatus().code > JamStatusCode.RUNNING:
        flash("You cannot unregister from a jam after it has finished.", "error")
        return redirect(jam.url())

    form = UnregisterJamForm()

    if form.validate_on_submit():
        get_current_user().leaveJam(jam)
        db.session.commit()
        flash("You are now unregistered from this jam.", "success")
        return redirect(jam.url())

    return render_template('jam/unregister.html', jam = jam, form = form)

@app.route('/jams/<jam_slug>/games/')
@path("Jams", "Games")
def jam_games(jam_slug):
    jam = Jam.query.filter_by(slug = jam_slug).first_or_404()
    return render_template('jam/games.html', jam = jam)

@app.route('/jams/<jam_slug>/participants/')
@path("Jams", "Participants")
def jam_participants(jam_slug):
    jam = Jam.query.filter_by(slug = jam_slug).first_or_404()
    return render_template('jam/participants.html', jam = jam)

@app.route('/jams/<jam_slug>/team_finder/toggle/')
def jam_toggle_show_in_finder(jam_slug):
    jam = Jam.query.filter_by(slug = jam_slug).first_or_404()
    r = get_current_user().getRegistration(jam)
    if not r: abort(404)
    r.show_in_finder = not r.show_in_finder
    db.session.commit()
    flash("You are now %s in the team finder for the jam \"%s\"." % ("shown" if r.show_in_finder else "hidden", jam.title), "success")
    return redirect(jam.url())

@app.route('/jams/<jam_slug>/team_finder/', methods=("GET", "POST"))
@path("Jams", "Team Finder")
def jam_team_finder(jam_slug):
    jam = Jam.query.filter_by(slug = jam_slug).first_or_404()
    form = TeamFinderFilter()
    l = []
    for r in jam.registrations:
        u = r.user
        if (not form.show_teamed.data) and r.team and (not r.team.isSingleTeam):
            continue # don't show teamed people

        if not r.show_in_finder:
            continue

        matches = 0

        if form.need_programmer.data and u.ability_programmer: matches += 1
        if form.need_gamedesigner.data and u.ability_gamedesigner: matches += 1
        if form.need_2dartist.data and u.ability_2dartist: matches += 1
        if form.need_3dartist.data and u.ability_3dartist: matches += 1
        if form.need_composer.data and u.ability_composer: matches += 1
        if form.need_sounddesigner.data and u.ability_sounddesigner: matches += 1

        if matches == 0 and not form.show_empty.data: continue

        l.append((r, matches))

    if form.order.data == "abilities":
        l.sort(key = lambda pair: pair[1], reverse = True)
    elif form.order.data == "location":
        l.sort(key = lambda pair: pair[0].user.location)
    else: # username
        l.sort(key = lambda pair: pair[0].user.username)

    return render_template('jam/team_finder.html', jam = jam, form = form, results = l)

@app.route('/jams/<jam_slug>/teams/')
@path("Jams", "Teams")
def jam_teams(jam_slug):
    jam = Jam.query.filter_by(slug = jam_slug).first_or_404()
    return render_template('jam/teams.html', jam = jam)

@app.route('/jams/<jam_slug>/teams/<int:team_id>/')
@path("Jams", "Team")
def jam_team(jam_slug, team_id):
    jam = Jam.query.filter_by(slug = jam_slug).first_or_404()
    team = Team.query.filter_by(id = team_id, jam_id = jam.id).first_or_404()
    return render_template('jam/team.html', jam = jam, team = team)

@app.route('/jams/<jam_slug>/team/devlog/', methods = ["POST", "GET"])
@app.route('/jams/<jam_slug>/team/devlog/<int:edit_id>', methods = ["POST", "GET"])
@path("Jams", "Team", "Write devlog")
def jam_devlog(jam_slug, edit_id = 0):
    require_login()
    jam = Jam.query.filter_by(slug = jam_slug).first_or_404()
    r = get_current_user().getRegistration(jam)
    if not r or not r.team: abort(403)

    form = DevlogForm()
    mode = "create"

    if edit_id:
        p = DevlogPost.query.filter_by(id = edit_id).first_or_404()
        if p.team != r.team: abort(403)
        mode = "edit"

    if form.validate_on_submit():
        if mode == "edit":
            p.title = form.title.data
            p.content = form.text.data
        else:
            p = DevlogPost(r.team, get_current_user(), form.title.data, form.text.data)
            db.session.add(p)
        db.session.commit()
        flash("Your post was successfully saved.", "success")
        return redirect(r.team.url())
    elif mode == "edit" and request.method == "GET":
        form.title.data = p.title
        form.text.data = p.content

    return render_template('jam/write_devlog.html', jam = jam, team = r.team, form = form, mode = mode, edit_id = edit_id)


@app.route('/jams/<jam_slug>/team/')
@path("Jams", "Team")
def jam_current_team(jam_slug):
    require_login()
    jam = Jam.query.filter_by(slug = jam_slug).first_or_404()
    user = get_current_user()
    r = user.getRegistration(jam)
    if r:
        return redirect(r.team.url())
    else:
        return redirect(jam.url())

@app.route('/jams/<jam_slug>/team/settings', methods = ["POST", "GET"])
@path("Jams", "Team")
def team_settings(jam_slug):
    require_login()

    settings_form = TeamSettingsForm()
    invite_form = InviteForm()
    invite_username = None

    jam = Jam.query.filter_by(slug = jam_slug).first_or_404()
    r = get_current_user().getRegistration(jam)
    if not r or not r.team: abort(404)
    team = r.team

    if settings_form.validate_on_submit():
        team.name = settings_form.name.data
        team.wip = settings_form.wip.data
        team.livestreams = settings_form.livestreams.data.strip()
        team.irc = settings_form.irc.data
        db.session.commit()
        flash("The team settings were saved.", "success")
        return redirect(team.url())
    elif invite_form.validate_on_submit():
        invite_username = invite_form.username.data
    elif request.method == "GET":
        settings_form.name.data = team.name
        settings_form.wip.data = team.wip
        settings_form.livestreams.data = team.livestreams
        settings_form.irc.data = team.irc

    if "invite" in request.args:
        invite_username = request.args["invite"]

    if invite_username:
        user = User.query.filter_by(username = invite_username, is_deleted = False).first()
        if not user:
            flash("Could not find user: %s" % invite_username, "error")
        elif user.inTeam(team):
            flash("User %s is already in this team." % invite_username, "warning")
        elif team.getInvitation(user):
            flash("User %s is already invited." % user.username, "warning")
        else:
            i = team.inviteUser(user, get_current_user())
            flash("Invited user %s." % invite_username, "success")

        return redirect(team.url())

    return render_template('jam/team_settings.html', team = team, invite_form = invite_form, settings_form = settings_form)

@app.route('/invitations/<int:id>', methods = ["POST", "GET"])
@app.route('/invitations/<int:id>/<action>', methods = ["POST", "GET"])
@path("Invitation")
def invitation(id, action = ""):
    invitation = Invitation.query.filter_by(id = id).first_or_404()
    require_user(invitation.user)

    if action == "accept":
        invitation.accept()
        flash("You have accepted the invitation.", "success")
        return redirect(invitation.team.url())
    elif action == "decline":
        invitation.decline()
        flash("You have declined the invitation.", "success")
        return redirect(invitation.team.url())
    else:
        return render_template("jam/invitation.html", invitation = invitation)

@app.route('/jams/<jam_slug>/delete', methods=("GET", "POST"))
@path("Jams", "Delete")
def delete_jam(jam_slug):
    require_admin()
    jam = Jam.query.filter_by(slug = jam_slug).first_or_404()

    # is this a confirmation?
    if request.method == "POST":
        # delete all the games for the jam
        for game in jam.games[:]:
            db.session.delete(game)

        db.session.delete(jam)
        db.session.commit()
        flash(jam.title +" was deleted", "success")
        return redirect('/')

    return render_template('delete_jam.html', jam = jam)

@app.route('/jams/<jam_slug>/countdown', methods=("GET", "POST"))
@path("Jams", "Countdown")
def countdown(jam_slug):
    jam = Jam.query.filter_by(slug = jam_slug).first_or_404()
    return render_template('misc/countdown.html', jam = jam)

@app.route('/jams/<jam_slug>/new_game', methods=("GET", "POST"))
@path("Jams", "New Game")
def new_game(jam_slug):
    require_login()
    return # INVALID STUFF HERE

    error = None
    form = SubmitEditGame()
    jam = Jam.query.filter_by(slug = jam_slug).first_or_404()

    if not 1 <= jam.getStatus().code <= 2:
        # new games only during the jam and the packaging phase
        flash("New games are not allowed at this time.", "error")
        return redirect(jam.url())

    # check if the user has already an game in this jam
    for game in jam.games:
        if game.user == get_current_user():
            flash("You already have an game for this jam. Look here!", "info")
            return redirect(game.url())
        elif get_current_user() in game.team:
            flash("You are part of this team! Leave the team to create your own game.", "error")
            return redirect(game.url())

    if form.validate_on_submit():
        title = form.name.data
        new_slug = models.get_slug(title)
        description = form.description.data
        if Game.query.filter_by(slug = new_slug, jam = jam).first():
            error = 'An game with a similar name already exists for this jam'
        else:
            new_game = Game(title, description, jam, get_current_user())
            db.session.add(new_game)
            db.session.commit()
            flash("Game submitted", "success")
            return redirect(new_game.url())
    return render_template('new_game.html', jam = jam, form = form, error = error)

@app.route('/jams/<jam_slug>/rate')
@app.route('/jams/<jam_slug>/rate/<action>', methods=("GET", "POST"))
@path("Jams", "Rate")
def rate_games(jam_slug, action = None):
    require_login()
    return # INVALID STUFF HERE

    jam = Jam.query.filter_by(slug = jam_slug).first_or_404()

    # Check whether jam is in rating period
    if jam.getStatus().code != 3:
        flash("Rating for this jam is closed.", "warning")
        return redirect(jam.url())

    error = None
    skip_form = SkipRating()
    rate_form = RateGame()
    # TODO: Filter for jams that match the the criteria to enable rating
    # (needs to happen during rating period only)
    # TODO: Keep track of who already rated

    if action == "submit_rating" and rate_form.validate_on_submit():
        game_id = rate_form.game_id.data
        game = Game.query.filter_by(id = game_id).first_or_404()

        # check if user can rate this game
        if not get_current_user().canRate(game):
            flash("You cannot rate your own game.", "error")
            return redirect(url_for("rate_games", jam_slug = jam.slug))

        # remove previous rating, if any
        edited = False
        if get_current_user().ratedGame(game):
            old_game = Rating.query.filter_by(game_id = game.id, user_id = get_current_user().id).first_or_404()
            db.session.delete(old_game)
            edited = True

        # remove skip mark, if any
        if get_current_user().skippedGame(game):
            rating_skip = RatingSkip.query.filter_by(game_id = game.id, user_id = get_current_user().id).first_or_404()
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
                note, game, get_current_user())
        db.session.add(new_rating)
        db.session.commit()
        flash("You rated for %s" % game.title, "success")
        return redirect(url_for('rate_games', jam_slug = jam.slug))

    elif action == "skip_rating" and skip_form.validate_on_submit():
        game_id = rate_form.game_id.data
        game = Game.query.filter_by(id = game_id).first_or_404()

        # error if you have already rated
        if get_current_user().ratedGame(game):
            flash("You already rated for %s." % game.title, "warning")
            return redirect(url_for("rate_games", jam_slug = jam.slug))

        # remove skip mark, if any
        if get_current_user().skippedGame(game):
            rating_skip = RatingSkip.query.filter_by(game_id = game.id, user_id = get_current_user().id).first_or_404()
            db.session.delete(rating_skip)

        # read data from form
        reason = skip_form.reason.data
        skip = RatingSkip(get_current_user(), game, reason)
        db.session.add(skip)
        db.session.commit()
        flash("You skipped rating for %s" % game.title, "info")
        return redirect(url_for('rate_games', jam_slug = jam.slug))

    # Find all games from this jam, including their rating count, ordered
    # by rating count ascending. Steps:
    # - select games
    # - also select their rating count and label this "rcount" for later sorting
    # - outer join with rating to get count even if there are no ratings
    # - group by game to count ratings PER GAME
    # - order by rating count, ascending (default)

    pairs = db.session.query(
            Game,
            db.func.count(Rating.id).label("rcount"))\
        .filter_by(jam_id = jam.id)\
        .outerjoin(Rating)\
        .group_by(Game.id)\
        .order_by("rcount")\
        .all()

    # Sort them into skipped, rated and "new" games (that's what we
    # call them for now)
    rated_games = []
    skipped_games = []
    new_games = []
    my_games = 0

    for pair in pairs:
        # ignore games by the user
        if get_current_user() == pair[0].user or get_current_user() in pair[0].team:
            my_games = my_games + 1
            continue

        if get_current_user().ratedGame(pair[0]):
            rated_games.append(pair)
        elif get_current_user().skippedGame(pair[0]):
            skipped_games.append(pair)
        else:
            new_games.append(pair)

    # Luckily, the lists are still sorted

    game = None
    is_skipped_game = False
    if new_games:
        # We got at least 1 new game. Take the first one.
        # TODO: Choose a random game if the lowest numbers of ratings is not
        # unique so that people rating at the same time might get different games
        # to rate on
        game = new_games[0][0]
    elif skipped_games:
        # We don't have any new games left, but some skipped ones. Take the first one.
        game = random.choice(skipped_games)[0]
        is_skipped_game = True

    if game:
        # We are going to display the form. Set the game id into the hidden fields.
        rate_form.game_id.data = game.id
        skip_form.game_id.data = game.id
        return render_template("rate_games.html", jam = jam, error = error,
            game = game, is_skipped_game = is_skipped_game, rate_form = rate_form,
            skip_form = skip_form, my_games = my_games)
    else:
        # We have nothing left to vote on
        flash("You have no games left to vote on. Thanks for participating.", "success")
        return redirect(jam.url())

@app.route('/jams/<jam_slug>/<game_slug>/reset_vote')
@path("Jams", "Rate", "Reset Vote")
def reset_vote(jam_slug, game_slug):
    require_login()
    jam = Jam.query.filter_by(slug = jam_slug).first_or_404()
    game = Game.query.filter_by(slug = game_slug).filter_by(jam = jam).first_or_404()
    rating = game.ratings.filter_by(user = get_current_user()).first_or_404()
    db.session.delete(rating)
    db.session.commit()
    flash("Your rating for this game has been reset. Visit the jam page to vote again.", "success")
    return redirect(game.url())

@app.route('/jams/<jam_slug>/<game_slug>/')
@app.route('/jams/<jam_slug>/<game_slug>/<action>', methods=("GET", "POST"))
@path("Jams", "Show Game")
def show_game(jam_slug, game_slug, action=None):
    comment_form = WriteComment()
    jam = Jam.query.filter_by(slug = jam_slug).first_or_404()
    game = Game.query.filter_by(slug = game_slug).filter_by(jam = jam).first_or_404()

    if action == "new_comment" and comment_form.validate_on_submit():
        require_login()
        text = comment_form.text.data
        new_comment = Comment(text, game, get_current_user())
        db.session.add(new_comment)
        db.session.commit()
        flash("Comment added", "success")
        return redirect(url_for('show_game', jam_slug = jam_slug, game_slug = game_slug))

    if action == "edit":
        require_user(game.team.members)
        error = ""
        edit_form = GameEditForm()
        if edit_form.validate_on_submit():
            title = edit_form.name.data
            new_slug = models.get_slug(title)
            description = edit_form.description.data
            old_game = Game.query.filter_by(slug = new_slug, jam = jam).first()
            if old_game and old_game != game:
                error = 'An game with a similar name already exists for this jam.'
            else:
                game.title = title
                game.slug = new_slug
                game.description = description
                db.session.commit()
                flash("Your changes have been saved.", "success")
                return redirect(game.url())
        elif request.method != "POST":
            edit_form.name.data = game.title
            edit_form.description.data = game.description

        return render_template('jam/game_edit.html', game = game, form = edit_form, error = error)

    if action == "add_screenshot":
        require_user(game.team.members)

        screen_form = GameAddScreenshot()
        if screen_form.validate_on_submit():
            s = gameScreenshot(screen_form.url.data, screen_form.caption.data, game)
            db.session.add(s)
            db.session.commit()
            flash("Your screenshot has been added.", "success")
            return redirect(game.url())

        return render_template("add_screenshot.html", game = game, form = screen_form)

    if action == "add_package":
        require_user(game.team.members)

        package_form = GameAddPackage()
        if package_form.validate_on_submit():
            s = GamePackage(game, package_form.url.data, package_form.type.data)
            db.session.add(s)
            db.session.commit()
            flash("Your package has been added.", "success")
            return redirect(game.url())

        return render_template("add_package.html", game = game, form = package_form)

    if action == "add_team_member":
        require_user(game.team.members)

        jam = Jam.query.filter_by(slug = jam_slug).first_or_404()
        if jam.team_jam == False:
            flash("This jam is not a team jam.", "error")
            return redirect(game.url())

        team_form = GameAddTeamMember()
        if team_form.validate_on_submit():
            member = User.query.filter_by(username = team_form.username.data).first_or_404()
            if member == get_current_user():
                flash("You cannot add yourself to the team.", "error")
            elif not member:
                flash("That username does not exist.", "error")
            elif member in game.team:
                flash("That user is already in the team.", "error")
            elif member.getGameInJam(game.jam):
                flash("That user has a game for this jam. Look here!", "error")
                return redirect(member.getGameInJam(game.jam).url())
            elif member.getTeamGameInJam(game.jam):
                flash("That user is already part of a team for this jam. Look here!", "error")
                return redirect(member.getTeamGameInJam(game.jam).url())
            else:
                game.team.append(member)
                db.session.commit()
                flash("%s has been added to the team." % member.username, "success")
                return redirect(game.url())

        return render_template("add_team_member.html", game = game, form = team_form)

    if action == "remove_screenshot":
        require_user(game.team.members)

        remove_id = request.args.get("remove_id", "")
        s = GameScreenshot.query.filter_by(game_id = game.id, id = remove_id).first_or_404()
        db.session.delete(s)
        db.session.commit()
        flash("The screenshot has been removed.", "success")
        return redirect(game.url())

    if action == "remove_package":
        require_user(game.team.members)

        remove_id = request.args.get("remove_id", "")
        s = GamePackage.query.filter_by(game_id = game.id, id = remove_id).first_or_404()
        db.session.delete(s)
        db.session.commit()
        flash("The package has been removed.", "success")
        return redirect(game.url())

    if action == "remove_team_member":
        require_user(game.team.members)

        jam = Jam.query.filter_by(slug = jam_slug).first_or_404()
        if jam.team_jam == False:
            flash("This jam is not a team jam.", "error")
            return redirect(game.url())

        remove_id = request.args.get("remove_id", "0")
        member = User.query.get(remove_id)
        db.session.commit()
        game.team.remove(member)
        db.session.commit()
        flash("%s has been removed from the team." % member.username, "success")
        return redirect(game.url())

    if action == "quit":
        require_user(game.team.members)

        jam = Jam.query.filter_by(slug = jam_slug).first_or_404()
        if jam.team_jam == False:
            flash("This jam is not a team jam.", "error")
            return redirect(game.url())

        game.team.remove(get_current_user())
        db.session.commit()
        flash("You have been removed from the team.", "success")
        return redirect(game.url())

    return render_template('jam/game.html', game=game, form = comment_form)

@app.route('/profile')
@path("Profile")
def profile():
    require_login()
    return render_template("account/profile.html", user = get_current_user())

@app.route('/users/<username>/')
@path("Profile")
def show_user(username):
    user = User.query.filter_by(is_deleted = False, username = username).first_or_404()
    return render_template("account/profile.html", user = user)

@app.route('/settings', methods = ["POST", "GET"])
@path("Profile", "Settings")
def settings():
    require_login()
    form = SettingsForm()
    user = get_current_user()
    logout = False

    if form.validate_on_submit():
        print "GO"
        user.ability_programmer = form.ability_programmer.data
        user.ability_gamedesigner = form.ability_gamedesigner.data
        user.ability_2dartist = form.ability_2dartist.data
        user.ability_3dartist = form.ability_3dartist.data
        user.ability_composer = form.ability_composer.data
        user.ability_sounddesigner = form.ability_sounddesigner.data
        user.abilities_extra = form.abilities_extra.data
        user.real_name = form.real_name.data
        user.about = form.about.data
        user.website = form.website.data
        user.pm_mode = form.pm_mode.data
        user.notify_new_jam = form.notify_new_jam.data
        user.notify_jam_start = form.notify_jam_start.data
        user.notify_jam_finish = form.notify_jam_finish.data
        user.notify_game_comment = form.notify_game_comment.data
        user.notify_team_changes = form.notify_team_changes.data
        user.notify_game_changes = form.notify_game_changes.data
        user.notify_team_invitation = form.notify_team_invitation.data
        user.notify_newsletter = form.notify_newsletter.data

        if user.location != form.location.data and form.location.data:
            new_loc, new_coords, new_flag = findLocation(form.location.data)
            if new_loc:
                user.location = form.location.data
                user.location_display = new_loc
                user.location_coords = new_coords
                user.location_flag = new_flag
                flash("Location was set to: " + new_loc, "success")
            else:
                flash("Could not find the location you entered.", "error")
        if not form.location.data:
            user.location = ""
            user.location_display = ""
            user.location_coords = ""
            user.location_flag = "unknown"

        if form.old_password.data and form.new_password.data and form.new_password2.data:
            if user.password != sha512((form.old_password.data + app.config['SECRET_KEY']).encode('utf-8')).hexdigest():
                flash("Your password is incorrect. The password was not changed.", "error")
            else:
                user.password = sha512((form.new_password.data + app.config['SECRET_KEY']).encode('utf-8')).hexdigest()
                flash("Your password was changed", "success")

        if user.email != form.email.data and form.email.data:
            user.new_email = form.email.data
            user.is_verified = False

            m = Mail("Please verify your new eMail address")
            m.addRecipientEmail(user.new_email)
            m.render("emails/account/verification.html", recipient = user, email_changed = True)
            m.send()

            logout = True
            flash("Your email address has changed. Please check your inbox for the verification.", "info")

        db.session.commit()
        flash("Your settings were saved.", "success")

        if logout:
            return redirect(url_for("logout"))
        else:
            return redirect(url_for("settings"))

    elif request.method == "GET":
        form.ability_programmer.data = user.ability_programmer
        form.ability_gamedesigner.data = user.ability_gamedesigner
        form.ability_2dartist.data = user.ability_2dartist
        form.ability_3dartist.data = user.ability_3dartist
        form.ability_composer.data = user.ability_composer
        form.ability_sounddesigner.data = user.ability_sounddesigner
        form.abilities_extra.data = user.abilities_extra
        form.real_name.data = user.real_name
        form.about.data = user.about
        form.website.data = user.website
        form.pm_mode.data = user.pm_mode
        form.location.data = user.location
        form.email.data = user.email
        form.notify_new_jam.data = user.notify_new_jam
        form.notify_jam_start.data = user.notify_jam_start
        form.notify_jam_finish.data = user.notify_jam_finish
        form.notify_game_comment.data = user.notify_game_comment
        form.notify_team_changes.data = user.notify_team_changes
        form.notify_game_changes.data = user.notify_game_changes
        form.notify_team_invitation.data = user.notify_team_invitation
        form.notify_newsletter.data = user.notify_newsletter

    return render_template('account/settings.html', form = form)

@app.route("/search")
@path("Search")
def search():
    q = request.args.get("q", "")
    if not q:
        return redirect(url_for("index"))

    jams = Jam.query.filter(db.or_(
        Jam.title.like("%"+q+"%"))).all()

    games = Game.query.filter(db.or_(
        Game.description.like("%"+q+"%"),
        Game.title.like("%"+q+"%"))).all()

    users = User.query.filter_by(is_deleted = False).filter(
        User.username.like("%"+q+"%")).all()

    j = len(jams)
    e = len(games)
    p = len(users)

    if j == 1 and e == 0 and p == 0:
        return redirect(jams[0].url())
    elif j == 0 and e == 1 and p == 0:
        return redirect(games[0].url())
    elif j == 0 and e == 0 and p == 1:
        return redirect(users[0].url())

    return render_template("misc/search.html", q = q, jams = jams, games = games, users = users)

@app.route('/contact')
@path("Contact")
def contact():
    return render_template('misc/contact.html')

@app.route('/rules')
@app.route('/rulez')
@path("Rules")
def rules():
    return render_template('misc/rules.html')

@app.route('/stats')
@app.route('/statistics')
@path("Statistics")
def statistics():
    # collect all the data
    stats = {}

    stats["total_jams"] = db.session.query(db.func.count(Jam.id)).first()[0];
    stats["total_users"] = db.session.query(db.func.count(User.id)).first()[0];

    all_jam_users = 0
    most_users_per_jam = 0
    most_users_jam = None
    most_games_per_jam = 0
    most_games_jam = None
    biggest_team_size = 0
    biggest_team_game = None

    for jam in Jam.query.all():
        users = 0
        for game in jam.games:
            teamsize = len(game.team.members) # for the author
            users += teamsize

            if teamsize > biggest_team_size:
                biggest_team_size = teamsize
                biggest_team_game = game

        if users > most_users_per_jam:
            most_users_per_jam = users
            most_users_jam = jam

        games = len(jam.games.all())
        if games > most_games_per_jam:
            most_games_per_jam = games
            most_games_jam = jam

        all_jam_users += users

    all_games = Game.query.all()
    finished_games = []
    for game in all_games:
      if game.jam.getStatus() == JamStatusCode.FINISHED:
        finished_games.append(game)
    finished_games.sort(cmp = gameCompare)
    stats["best_games"] = finished_games[:3]

    user_most_games = User.query.filter_by(is_deleted = False).all()
    user_most_games.sort(cmp = userTotalGameCompare)
    stats["user_most_games"] = user_most_games[:3]

    if stats["total_jams"]: # against division by zero
        stats["average_users"] = all_jam_users * 1.0 / stats["total_jams"];
    else:
        stats["average_users"] = 0
    stats["most_users_per_jam"] = most_users_per_jam
    stats["most_users_jam"] = most_users_jam

    stats["total_games"] = db.session.query(db.func.count(Game.id)).first()[0];
    if stats["total_jams"]: # against division by zero
        stats["average_games"] = stats["total_games"] * 1.0 / stats["total_jams"]
    else:
        stats["average_games"] = 0
    stats["most_games_per_jam"] = most_games_per_jam
    stats["most_games_jam"] = most_games_jam

    if stats["average_games"]: # against division by zero
        stats["average_team_size"] = stats["average_users"] * 1.0 / stats["average_games"]
    else:
        stats["average_team_size"] = 0
    stats["biggest_team_size"] = biggest_team_size
    stats["biggest_team_game"] = biggest_team_game


    #Best rated games
    #User with most games

    return render_template('misc/statistics.html', stats = stats)

@app.route('/announcements')
@path("Announcements")
def announcements():
    announcements = Announcement.query.order_by(Announcement.posted.desc())
    return render_template('announcements.html', announcements = announcements)

@app.route('/faq')
@app.route('/faq/<page>')
@path("FAQ")
def faq(page = ""):
    if page.lower() == "packaging":
        return render_template('misc/faq_packaging.html')
    return render_template('misc/faq.html')

@app.route('/links')
@path("Links")
def links():
    return render_template('misc/links.html')

@app.route('/subreddit')
@path("Subreddit")
def subreddit():
    return redirect("http://www.reddit.com/r/bacongamejam")

@app.errorhandler(404)
@app.errorhandler(403)
@app.errorhandler(500)
@path("Error")
def error(error):
    return render_template("error.html", error = error), error.code

@app.errorhandler(smtplib.SMTPRecipientsRefused)
@path("Error")
def invalid_email(exception):
    flash("Invalid email address.", "error")
    return redirect(url_for('login'))

@app.errorhandler(flamejam.login.LoginRequired)
@path("Error")
def login_required(exception):
    flash(exception.message, "error")
    return redirect(url_for('login', next = exception.next))






# ADMIN PANEL

@app.route("/admin")
def admin_index():
    return redirect(url_for('admin_users'))

@app.route("/admin/users")
def admin_users():
    require_admin()
    users = User.query.all()
    return render_template("admin/users.html", users = users)

@app.route("/admin/users/form", methods = ["POST"])
def admin_users_form():
    require_admin()

    users = []
    for field in request.form:
        print field
        if field[:5] == "user-" and request.form[field] == "on":
            i = field[5:]
            users.append(User.query.filter_by(id = i).first_or_404())

    for user in users:
        if request.form["submit"] == "Toggle Deleted":
            user.is_deleted = not user.is_deleted
        if request.form["submit"] == "Toggle Admin":
            user.is_admin = not user.is_admin

    db.session.commit()

    flash(str(len(users)) + " users were deleted", "success")

    return redirect(url_for("admin_users"))

@app.route("/admin/users/<username>")
@app.route("/admin/user/<username>")
def admin_user(username):
    require_admin()
    user = User.query.filter_by(username = username).first_or_404()
    return render_template("admin/user.html", user = user)

@app.route("/admin/jams")
def admin_jams():
    require_admin()
    return render_template("admin/jams.html", jams = Jam.query.all())


@app.route("/admin/jams/<int:id>", methods = ["POST", "GET"])
@app.route("/admin/jams/create/", methods = ["POST", "GET"])
def admin_jam(id = 0):
    require_admin()
    mode = "create"
    jam = None

    if id != 0:
        jam = Jam.query.filter_by(id = id).first_or_404()
        mode = "edit"

    form = JamDetailsForm()

    if form.validate_on_submit():
        slug_jam = Jam.query.filter_by(slug = get_slug(form.title.data.strip())).first()
        if slug_jam and slug_jam != jam:
            flash("A jam with a similar title already exists (slug conflict).", "error")
        else:
            if mode == "create":
                jam = Jam("", datetime.utcnow())
                db.session.add(jam)

            jam.title = form.title.data.strip()
            jam.slug = get_slug(jam.title)

            jam.theme = form.theme.data.strip()
            jam.team_limit = form.team_limit.data
            jam.start_time = form.start_time.data
            jam.registration_duration = form.registration_duration.data
            jam.packaging_duration = form.packaging_duration.data
            jam.rating_duration = form.rating_duration.data
            jam.duration = form.duration.data
            jam.description = form.description.data.strip()
            jam.restrictions = form.restrictions.data.strip()

            db.session.commit()
            flash("Jam settings have been saved.", "success")
            return redirect(url_for("admin_jam", id = jam.id))
    elif request.method == "GET" and mode == "edit":
        form.title.data = jam.title
        form.theme.data = jam.theme
        form.team_limit.data = jam.team_limit
        form.start_time.data = jam.start_time
        form.registration_duration.data = jam.registration_duration
        form.packaging_duration.data = jam.packaging_duration
        form.rating_duration.data = jam.rating_duration
        form.duration.data = jam.duration
        form.description.data = jam.description
        form.restrictions.data = jam.restrictions

    return render_template("admin/jam.html", id = id, mode = mode, jam = jam, form = form)

@app.route("/admin/announcements")
def admin_announcements():
    require_admin()

    return render_template("admin/announcements.html", announcements = Announcement.query.all())

@app.route("/admin/announcement", methods = ["GET", "POST"])
def admin_announcement():
    require_admin()

    form = AdminWriteAnnouncement()

    if form.validate_on_submit():
        announcement = Announcement(form.message.data)
        announcement.subject = form.subject.data
        announcement.context = "newsletter"
        announcement.sendMail()
        flash("Your announcement has been sent to the users.")

    return render_template("admin/announcement.html", form = form)


@app.route("/ajax/markdown", methods = ["POST"])
def ajax_markdown():
    return str(markdown_object(request.form["input"]))
