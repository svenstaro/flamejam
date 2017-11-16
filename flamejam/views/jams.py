from flamejam import app, db
from flamejam.models.jam import Jam, JamStatusCode
from flamejam.models.gamepackage import GamePackage
from flamejam.forms import ParticipateForm, CancelParticipationForm, TeamFinderFilter
from flask import render_template, redirect, flash, request, abort
from flask_login import login_required, current_user


@app.route('/jams/')
def jams():
    return render_template("misc/search.html", jams=Jam.query.all())


@app.route('/jams/<jam_slug>/')
def jam_info(jam_slug):
    jam = Jam.query.filter_by(slug=jam_slug).first_or_404()
    return render_template('jam/info.html', jam=jam)


@app.route('/jams/<jam_slug>/countdown')
def countdown(jam_slug):
    jam = Jam.query.filter_by(slug=jam_slug).first_or_404()
    return render_template('misc/countdown.html', jam=jam)


@app.route('/jams/<jam_slug>/participate/', methods=["POST", "GET"])
@login_required
def jam_participate(jam_slug):
    jam = Jam.query.filter_by(slug=jam_slug).first_or_404()
    user = current_user

    if jam.get_status().code > JamStatusCode.PACKAGING:
        flash("You cannot register for participation in a jam after it has finished or "
              "is in rating phase.", "error")
        return redirect(jam.url())

    if jam.get_status().code < JamStatusCode.REGISTRATION:
        flash("You cannot register for participation before the registration started.", "error")
        return redirect(jam.url())

    if user.get_participation(jam):
        flash("You already participate in this jam.", "warning")
        return redirect(jam.url())

    form = ParticipateForm()

    if form.validate_on_submit():
        user.join_jam(jam)
        user.get_participation(jam).show_in_finder = form.show_in_finder.data
        db.session.commit()
        flash("You are now registered for this jam.", "success")
        return redirect(jam.url())

    return render_template('jam/participate.html', jam=jam, form=form)


@app.route('/jams/<jam_slug>/cancel-participation/', methods=["POST", "GET"])
@login_required
def jam_cancel_participation(jam_slug):
    jam = Jam.query.filter_by(slug=jam_slug).first_or_404()

    if jam.get_status().code > JamStatusCode.PACKAGING:
        flash("You cannot unregister from a jam after it has finished or is in rating phase.",
              "error")
        return redirect(jam.url())

    form = CancelParticipationForm()

    if form.validate_on_submit():
        current_user.leave_jam(jam)
        db.session.commit()
        flash("You are now unregistered from this jam.", "success")
        return redirect(jam.url())

    return render_template('jam/cancel_participation.html', jam=jam, form=form)


@app.route('/jams/<jam_slug>/games/')
def jam_games(jam_slug):
    jam = Jam.query.filter_by(slug=jam_slug).first_or_404()
    filters = set(request.args['filter'].split(' ')) if 'filter' in request.args else set()
    games = jam.games_by_score(filters) if jam.show_ratings else jam.games_by_total_ratings(filters)
    return render_template('jam/games.html', jam=jam, games=games, filters=filters,
                           package_types=GamePackage.package_types(),
                           type_string_short=GamePackage.type_string_short)


@app.route('/jams/<jam_slug>/participants/')
def jam_participants(jam_slug):
    jam = Jam.query.filter_by(slug=jam_slug).first_or_404()
    return render_template('jam/participants.html', jam=jam)


@app.route('/jams/<jam_slug>/team_finder/toggle/')
def jam_toggle_show_in_finder(jam_slug):
    jam = Jam.query.filter_by(slug=jam_slug).first_or_404()
    r = current_user.get_participation(jam)
    if not r:
        abort(404)
    r.show_in_finder = not r.show_in_finder
    db.session.commit()
    shown_or_hidden = "shown" if r.show_in_finder else "hidden"
    flash(f"You are now {shown_or_hidden} in the team finder for the jam '{jam.title}'", "success")
    return redirect(jam.url())


@app.route('/jams/<jam_slug>/team_finder/', methods=("GET", "POST"))
def jam_team_finder(jam_slug):
    jam = Jam.query.filter_by(slug=jam_slug).first_or_404()
    form = TeamFinderFilter()
    lst = []
    for r in jam.participations:
        u = r.user
        if (not form.show_teamed.data) and r.team and (not r.team.isSingleTeam):
            continue  # don't show teamed people

        if not r.show_in_finder:
            continue

        matches = 0

        if form.need_programmer.data and u.ability_programmer:
            matches += 1
        if form.need_gamedesigner.data and u.ability_gamedesigner:
            matches += 1
        if form.need_2dartist.data and u.ability_2dartist:
            matches += 1
        if form.need_3dartist.data and u.ability_3dartist:
            matches += 1
        if form.need_composer.data and u.ability_composer:
            matches += 1
        if form.need_sounddesigner.data and u.ability_sounddesigner:
            matches += 1

        if matches == 0 and not form.show_empty.data:
            continue

        lst.append((r, matches))

    if form.order.data == "abilities":
        lst.sort(key=lambda pair: pair[1], reverse=True)
    elif form.order.data == "location":
        lst.sort(key=lambda pair: pair[0].user.location)
    else:  # username
        lst.sort(key=lambda pair: pair[0].user.username)

    return render_template('jam/team_finder.html', jam=jam, form=form, results=lst)
