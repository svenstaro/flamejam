from flamejam import app, db
from flamejam.login import *
from flamejam.models import Jam, Game, User, Comment, GamePackage, GameScreenshot, JamStatusCode
from flamejam.forms import WriteComment, GameEditForm, GameAddScreenshotForm, GameAddPackageForm, GameAddTeamMemberForm, GameCreateForm
from flask import render_template, url_for, redirect, flash

@app.route("/jams/<jam_slug>/create-game/", methods = ("GET", "POST"))
def create_game(jam_slug):
    jam = Jam.query.filter_by(slug = jam_slug).first_or_404()
    r = get_current_user().getRegistration(jam)
    if not r or not r.team:
        flash("You cannot create a game without being registered for the jam.", category = "error")
        return redirect(jam.url())
    if r.team.game:
        flash("You already have a game.")
        return redirect(r.team.game.url())

    enabled = (JamStatusCode.RUNNING <= jam.getStatus().code <= JamStatusCode.PACKAGING)

    form = GameCreateForm(request.form, obj = None)
    if enabled and form.validate_on_submit():
        game = Game(r.team, form.title.data)
        db.session.add(game)
        db.session.commit()
        return redirect(url_for("edit_game", jam_slug = jam_slug, game_slug = game.slug))

    return render_template("jam/game/create.html", jam = jam, enabled = enabled, form = form)

@app.route("/jams/<jam_slug>/<game_slug>/edit/", methods = ("GET", "POST"))
def edit_game(jam_slug, game_slug):
    jam = Jam.query.filter_by(slug = jam_slug).first_or_404()
    game = jam.games.filter_by(slug = game_slug).first_or_404()

    require_user(game.team.members)

    form = GameEditForm(request.form, obj = game)
    package_form = GameAddPackageForm()
    screenshot_form = GameAddScreenshotForm()

    if form.validate_on_submit():
        print "OMG"
        slug = get_slug(form.title.data)
        print slug
        if not jam.games.filter_by(slug = slug).first() in (game, None):
            flash("A game with a similar title already exists. Please choose another title.", category = "error")
        else:
            form.populate_obj(game)
            print form.help.data
            game.slug = get_slug(game.title)
            db.session.commit()
            flash("Your settings have been applied.", category = "success")
            return redirect(game.url())

    if package_form.validate_on_submit():
        s = GamePackage(game, package_form.url.data, package_form.type.data)
        db.session.add(s)
        db.session.commit()
        flash("Your package has been added.", "success")
        return redirect(request.url)

    if screenshot_form.validate_on_submit():
        s = GameScreenshot(screenshot_form.url.data, screenshot_form.caption.data, game)
        db.session.add(s)
        db.session.commit()
        flash("Your screenshot has been added.", "success")
        return redirect(request.url)

    return render_template("jam/game/edit.html", jam = jam, game = game,
        form = form, package_form = package_form, screenshot_form = screenshot_form)

@app.route('/edit/package/<id>/<action>/')
def game_package_edit(id, action):
    if not action in ("delete"):
        abort(404)

    p = GamePackage.query.filter_by(id = id).first_or_404()
    require_user(p.game.team.members)

    if action == "delete":
        db.session.delete(p)
    db.session.commit()
    return redirect(url_for("edit_game", jam_slug = p.game.jam.slug, game_slug = p.game.slug))

@app.route('/edit/screenshot/<id>/<action>/')
def game_screenshot_edit(id, action):
    if not action in ("up", "down", "delete"):
        abort(404)

    s = GameScreenshot.query.filter_by(id = id).first_or_404()
    require_user(s.game.team.members)

    if action == "up":
        s.move(-1)
    elif action == "down":
        s.move(1)
    elif action == "delete":
        db.session.delete(s)
        i = 0
        for x in s.game.screenshotsOrdered:
            x.index = i
            i += 1
    db.session.commit()
    return redirect(url_for("edit_game", jam_slug = s.game.jam.slug, game_slug = s.game.slug))

@app.route('/jams/<jam_slug>/<game_slug>/')
def show_game(jam_slug, game_slug):
    comment_form = WriteComment()
    jam = Jam.query.filter_by(slug = jam_slug).first_or_404()
    game = Game.query.filter_by(slug = game_slug).filter_by(jam = jam).first_or_404()
    return render_template('jam/game/info.html', game = game, form = comment_form)

    """
    if action == "new_comment" and comment_form.validate_on_submit():
        require_login()
        text = comment_form.text.data
        new_comment = Comment(text, game, get_current_user())
        db.session.add(new_comment)
        db.session.commit()
        flash("Comment added", "success")
        return redirect(url_for('show_game', jam_slug = jam_slug, game_slug = game_slug))

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
    """

