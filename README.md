flamejam - a game jam application using Flask
=============================================

Description
-----------
flamejam is a generic game jam application that uses the Flask microframework.
It was initially created as a voting platforms for the [Reddit Game Jam](http://www.reddit.com/r/RedditGameJam). However,
it is generic and as such it is usable for any other game jam event.

This application is designed to make sure that participants vote on other
entries fairly and evenly. This is achieved by only presenting one game at a
time to vote on.

Dependencies
------------
You will need

 - Python 2.7
 - flask
 - flask-sqlalchemy
 - flask-wtforms
 - flask-login

as well as their respective dependencies. I recommend using a virtualenv and pip
to install all of those.

Running
-------
Run `python runserver` to fire up the debug server and navigate to
http://localhost:5000
