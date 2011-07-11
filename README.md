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

License
-------
This application, all of its sources and resources are licensed under the zlib license with the
following exceptions:

 - jquery
 - lightbox
 - 8-bit Reddit alien
 - Reddit alien drawing on error page

These exceptions are subject to their own copyrights and licenses. This project only makes use of them.

For the full license text, please see the included LICENSE file.

Dependencies
------------
You will need

 - Python 2.7
 - flask
 - flask-sqlalchemy
 - flask-wtf
 - flask-login
 - flask-markdown
 - python-dateutil

as well as their respective dependencies. I recommend using a virtualenv and pip
to install all of those.

Running
-------
Run `python runserver` to fire up the debug server and navigate to
http://localhost:5000
