import traceback

from flask.ext.mail import Message
from flask.ext.principal import PermissionDenied
from smtplib import SMTPRecipientsRefused

from flamejam import app, db, mail
from flamejam.models import Jam, User, Team, Game, JamStatusCode
from flask import render_template, request, url_for, redirect

@app.errorhandler(404)
@app.errorhandler(403)
@app.errorhandler(PermissionDenied)
def error(error):
    code = error.code if hasattr(error, "code") else 403
    return render_template("error.html", error = error, code = code), code

@app.errorhandler(500)
def application_error(error):
    msg = Message("[%s] Exception Detected: %s" % (app.config['SHORT_NAME'], error.message),
                    recipients=app.config['ADMINS'])
    msg_contents = [
        'Traceback:',
        '='*80,
        traceback.format_exc(),
    ]
    msg_contents.append('\n')
    msg_contents.append('Request Information:')
    msg_contents.append('='*80)
    environ = request.environ
    environkeys = sorted(environ.keys())
    for key in environkeys:
        msg_contents.append('%s: %s' % (key, environ.get(key)))

    msg.body = '\n'.join(msg_contents) + '\n'

    mail.send(msg)
    return error(error)

@app.errorhandler(SMTPRecipientsRefused)
def invalid_email(exception):
    flash("Invalid email address.", "error")
    return redirect(url_for('login'))

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

@app.route("/search")
def search():
    q = request.args.get("q", "")
    if not q:
        return redirect(url_for("index"))
    like = "%" + q + "%"

    jams = Jam.query.filter(db.or_(
        Jam.title.like(like))).all()

    games = Game.query.filter(db.or_(
        Game.description.like(like),
        Game.title.like(like))).all()

    users = User.query.filter_by(is_deleted = False).filter(
        User.username.like(like)).all()

    total = len(jams) + len(games) + len(users)

    if len(jams) == total == 1:
        return redirect(jams[0].url())
    elif len(games) == total == 1:
        return redirect(games[0].url())
    elif len(users) == total == 1:
        return redirect(users[0].url())

    return render_template("misc/search.html", q = q, jams = jams, games = games, users = users)

@app.route('/contact')
def contact():
    return render_template('misc/contact.html')

@app.route('/rules')
@app.route('/rulez')
def rules():
    return render_template('misc/rules.html')

@app.route('/stats')
@app.route('/statistics')
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
    finished_games.sort(key = Game.score.fget, reverse = True)
    stats["best_games"] = finished_games[:3]

    user_most_games = User.query.filter_by(is_deleted = False).all()
    user_most_games.sort(key = User.numberOfGames, reverse = True)
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

@app.route('/faq')
@app.route('/faq/<page>')
def faq(page = ""):
    if page.lower() == "packaging":
        return render_template('misc/faq_packaging.html')
    return render_template('misc/faq.html')

@app.route('/links')
def links():
    return render_template('misc/links.html')

@app.route('/subreddit')
def subreddit():
    return redirect("http://www.reddit.com/r/bacongamejam")

@app.route('/tick')
def tick():
    """This function is meant to be called regularly by a cronjob.
    Its purpose is to send out mails and do site maitenance even
    when there are no visitors.

    Your cronjob could look like this:
    * * * * * /usr/bin/curl http://domain.tld/tick
    """

    msg = ""

    # Send Notifications
    for jam in Jam.query.all():
        n = jam.sendAllNotifications()
        if n >= 0:
            msg += "sending notification " + str(n) + " on jam " + jam.slug + "\n"

    # Delete unverified users
    for user in User.query.filter_by(is_verified = False):
        # new_mail is set on users that *changed* their address
        if not user.new_email and user.registered < datetime.utcnow() - timedelta(days=7):
            msg += "deleted user " + user.username + " for being unverified too long\n"
            db.session.delete(user)

    # Remove invitations after game rating has started
    for jam in Jam.query.all():
        if jam.getStatus().code >= JamStatusCode.RATING:
            for team in jam.teams.all():
                for i in team.invitations.all():
                    msg += "deleted invitation " + str(i.id) + " on jam " + jam.slug + " - jam rating has started\n"
                    db.session.delete(i)

    db.session.commit()

    return msg
