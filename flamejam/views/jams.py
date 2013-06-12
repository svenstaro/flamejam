from flamejam import app, db
from flamejam.models import Jam, JamStatusCode, GamePackage
from flamejam.forms import RegisterJamForm, UnregisterJamForm, TeamFinderFilter
from flask import render_template, url_for, redirect, flash, request
from flask.ext.login import login_required, current_user

@app.route('/jams/')
def jams():
    return render_template("misc/search.html", jams = Jam.query.all())

@app.route('/jams/<jam_slug>/', methods=("GET", "POST"))
def jam_info(jam_slug):
    jam = Jam.query.filter_by(slug = jam_slug).first_or_404()
    return render_template('jam/info.html', jam = jam)

@app.route('/jams/<jam_slug>/countdown', methods=("GET", "POST"))
def countdown(jam_slug):
    jam = Jam.query.filter_by(slug = jam_slug).first_or_404()
    return render_template('misc/countdown.html', jam = jam)

@app.route('/jams/<jam_slug>/register/', methods = ["POST", "GET"])
@login_required
def jam_register(jam_slug):
    jam = Jam.query.filter_by(slug = jam_slug).first_or_404()
    user = current_user

    if jam.getStatus().code > JamStatusCode.RUNNING:
        flash("You cannot register for a jam after it has finished.", "error")
        return redirect(jam.url())

    if jam.getStatus().code < JamStatusCode.REGISTRATION:
        flash("You cannot register before the registration started.", "error")
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
@login_required
def jam_unregister(jam_slug):
    jam = Jam.query.filter_by(slug = jam_slug).first_or_404()

    if jam.getStatus().code > JamStatusCode.RUNNING:
        flash("You cannot unregister from a jam after it has finished.", "error")
        return redirect(jam.url())

    form = UnregisterJamForm()

    if form.validate_on_submit():
        current_user.leaveJam(jam)
        db.session.commit()
        flash("You are now unregistered from this jam.", "success")
        return redirect(jam.url())

    return render_template('jam/unregister.html', jam = jam, form = form)

@app.route('/jams/<jam_slug>/games/')
def jam_games(jam_slug):
    jam = Jam.query.filter_by(slug = jam_slug).first_or_404()
    filters = set(request.args['filter'].split(' ')) if 'filter' in request.args else set()
    games = jam.gamesByScore(filters) if jam.showRatings else jam.gamesByTotalRatings(filters)
    return render_template('jam/games.html', jam = jam, games = games, filters = filters, package_types = GamePackage.packageTypes(), typeStringShort = GamePackage.typeStringShort)

@app.route('/jams/<jam_slug>/participants/')
def jam_participants(jam_slug):
    jam = Jam.query.filter_by(slug = jam_slug).first_or_404()
    return render_template('jam/participants.html', jam = jam)

@app.route('/jams/<jam_slug>/team_finder/toggle/')
def jam_toggle_show_in_finder(jam_slug):
    jam = Jam.query.filter_by(slug = jam_slug).first_or_404()
    r = current_user.getRegistration(jam)
    if not r: abort(404)
    r.show_in_finder = not r.show_in_finder
    db.session.commit()
    flash("You are now %s in the team finder for the jam \"%s\"." % ("shown" if r.show_in_finder else "hidden", jam.title), "success")
    return redirect(jam.url())

@app.route('/jams/<jam_slug>/team_finder/', methods=("GET", "POST"))
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
