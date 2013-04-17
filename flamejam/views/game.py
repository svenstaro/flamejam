from flamejam import app, db
from flamejam.models import Jam, Game, User, Comment, GamePackage, GameScreenshot
from flamejam.forms import WriteComment, GameEditForm, GameAddScreenshotForm, GameAddPackageForm, GameAddTeamMemberForm
from flask import render_template, url_for, redirect, flash

@app.route('/jams/<jam_slug>/<game_slug>/')
@app.route('/jams/<jam_slug>/<game_slug>/<action>', methods=("GET", "POST"))
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

