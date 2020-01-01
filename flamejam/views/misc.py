import traceback
from datetime import datetime, timedelta

from flask_mail import Message
from flask_principal import PermissionDenied
from smtplib import SMTPRecipientsRefused

from flamejam import app, db, mail
from flamejam.models.jam import Jam, JamStatusCode
from flamejam.models.user import User
from flamejam.models.team import Team
from flamejam.models.game import Game
from flamejam.utils import get_current_jam
from flask import render_template, request, url_for, redirect, flash, jsonify
from werkzeug.exceptions import Forbidden, InternalServerError


@app.errorhandler(404)
@app.errorhandler(403)
def error(e):
    return render_template("error.html", error=e), e.code


@app.errorhandler(PermissionDenied)
def error_permission(e):
    return error(Forbidden())


@app.errorhandler(500)
def application_error(e):
    msg = Message(f"[{app.config['SHORT_NAME']}] Exception Detected: {str(e)}",
                  recipients=app.config['ADMINS'])
    msg_contents = [
        'Traceback:',
        '='*80,
        traceback.format_exc(),
        '\n',
        'Request Information:',
        '='*80
    ]
    environ = request.environ
    environkeys = sorted(environ.keys())
    for key in environkeys:
        msg_contents.append('%s: %s' % (key, environ.get(key)))

    msg.body = '\n'.join(msg_contents) + '\n'

    mail.send(msg)
    return error(InternalServerError())


@app.errorhandler(SMTPRecipientsRefused)
def invalid_email(exception):
    flash("Invalid email address.", "error")
    return redirect(url_for('login'))


@app.route("/map")
@app.route("/map/<mode>")
@app.route("/map/<mode>/<int:id>")
def map(mode="users", id=0):
    users = []
    extra = None
    if mode == "jam":
        extra = Jam.query.filter_by(id=id).first_or_404()
        users = extra.participants
    elif mode == "user":
        extra = User.query.filter_by(id=id).first_or_404()
        users = [extra]
    elif mode == "team":
        extra = Team.query.filter_by(id=id).first_or_404()
        users = extra.members
    else:
        mode = "users"
        users = User.query.all()

    x = 0
    for user in users:
        if user.location_coords:
            x += 1

    return render_template("misc/map.html", users=users, mode=mode, extra=extra, x=x)


@app.route("/search")
def search():
    q = request.args.get("q", "")
    if not q:
        return redirect(url_for("index"))
    like = "%" + q + "%"

    jams = Jam.query.filter(db.or_(
        Jam.title.like(like))).all()

    games = Game.query.filter_by(is_deleted=False).filter(
        db.or_(Game.description.like(like),
               Game.title.like(like))).all()

    users = User.query.filter_by(is_deleted=False).filter(
        User.username.like(like)).all()

    total = len(jams) + len(games) + len(users)

    if len(jams) == total == 1:
        return redirect(jams[0].url())
    elif len(games) == total == 1:
        return redirect(games[0].url())
    elif len(users) == total == 1:
        return redirect(users[0].url())

    return render_template("misc/search.html", q=q, jams=jams, games=games, users=users)


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

    stats["total_jams"] = Jam.query.count()
    stats["total_users"] = User.query.count()

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
            if not game.is_deleted:
                teamsize = len(game.team.members)  # for the author
                users += teamsize

                if teamsize > biggest_team_size:
                    biggest_team_size = teamsize
                    biggest_team_game = game

        if users > most_users_per_jam:
            most_users_per_jam = users
            most_users_jam = jam

        games = Game.query.filter_by(is_deleted=False).count()

        if games > most_games_per_jam:
            most_games_per_jam = games
            most_games_jam = jam

        all_jam_users += users

    all_games = Game.query.filter_by(is_deleted=False).all()
    finished_games = []
    for game in all_games:
        if game.jam.get_status() == JamStatusCode.FINISHED:
            finished_games.append(game)
    finished_games.sort(key=Game.score.fget, reverse=True)
    stats["best_games"] = finished_games[:3]

    user_most_games = User.query.filter_by(is_deleted=False).all()
    user_most_games.sort(key=User.number_of_games, reverse=True)
    stats["user_most_games"] = user_most_games[:3]

    if stats["total_jams"]:  # against division by zero
        stats["average_users"] = all_jam_users * 1.0 / stats["total_jams"]
    else:
        stats["average_users"] = 0
    stats["most_users_per_jam"] = most_users_per_jam
    stats["most_users_jam"] = most_users_jam

    stats["total_games"] = Game.query.filter_by(is_deleted=False).count()
    if stats["total_jams"]:  # against division by zero
        stats["average_games"] = stats["total_games"] * 1.0 / stats["total_jams"]
    else:
        stats["average_games"] = 0
    stats["most_games_per_jam"] = most_games_per_jam
    stats["most_games_jam"] = most_games_jam

    if stats["average_games"]:  # against division by zero
        stats["average_team_size"] = stats["average_users"] * 1.0 / stats["average_games"]
    else:
        stats["average_team_size"] = 0
    stats["biggest_team_size"] = biggest_team_size
    stats["biggest_team_game"] = biggest_team_game

    return render_template('misc/statistics.html', stats=stats)


@app.route('/faq')
@app.route('/faq/<page>')
def faq(page=""):
    if page.lower() == "packaging":
        return render_template('misc/faq_packaging.html')
    return render_template('misc/faq.html')


@app.route('/links')
def links():
    return render_template('misc/links.html')


@app.route('/subreddit')
def subreddit():
    return redirect("http://www.reddit.com/r/bacongamejam")


@app.route('/current_jam_info')
def current_jam_info():
    jam = get_current_jam()
    return jsonify(slug=jam.slug,
                   title=jam.title,
                   announced=str(jam.announced),
                   start_time=str(jam.start_time),
                   duration=jam.duration,
                   team_limit=jam.team_limit,
                   participants_count=len(jam.participations),
                   teams_count=len(jam.teams))


@app.route('/site_info')
def site_info():
    stats = {}
    stats["total_jams"] = db.session.query(db.func.count(Jam.id)).first()[0]
    stats["total_users"] = db.session.query(db.func.count(User.id)).first()[0]
    stats["total_games"] = db.session.query(db.func.count(not Game.is_deleted)).first()[0]
    return jsonify(total_jams=stats["total_jams"],
                   total_users=stats["total_users"],
                   total_games=stats["total_games"],
                   subreddit=url_for('subreddit', _external=True),
                   rules=url_for('rules', _external=True))
