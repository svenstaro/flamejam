flamejam - a game jam application using Flask
=============================================

Description
-----------
flamejam is a generic game jam application that uses the Flask microframework.
It was initially created as a voting platforms for the [BaconGameJam](http://www.reddit.com/r/BaconGameJam).
However, it is generic and as such it is usable for any other game jam event.

This application is designed to make sure that participants vote on other
entries fairly and evenly.

Dependencies
------------
You will need

 - Python 2.7
 - virtualenv
 - pip
 - flask
 - flask-mail
 - flask-sqlalchemy
 - flask-wtf
 - flask-login
 - flask-markdown
 - python-dateutil
 - scrypt
 - requests
 - alembic
 - flask-principal
 - mysql-python

as well as their respective dependencies. All of these are available on PYPI and as such
I recommend using a virtualenv and pip to install all of those. Always get the newest version
of any of these. If flamejam should be incompatible with the latest version of one of these
packages, it is to be considered a bug and should be fixed.

Installation
------------
You are currently expected to run some kind of POSIX system such as Linux. This software has
not been tested on Windows and it would be quite a wonder indeed if it worked there.

1.  The installation should generally be rather simple provided you have virtualenv and pip in
    your PATH. Should that be the case, it would be as simple as running

        # make install

    True enough, this will install the software directly to your system and set up all the dependencies
    for you in a virtualenv. Should you want to install to a different root, use something like

        # make DESTDIR=/some/else install

2.  Copy the default config from `/usr/share/doc/flamejam/flamejam.cfg.default` to
    `/etc/flamejam/flamejam.cfg` and configure it to your needs. Do not forget to set permissions
    accordingly as this file contains cleartext passwords.
3.  Copy the cron file from `/usr/share/doc/flamejam/flamejam.cron.d` to `/etc/cron.d/flamejam`.
    This cronjob will tick the web app every minute and send out announcements on time if needed.
4.  Configure your webserver. If you use Apache with mod\_wsgi, you may use the provided example
    virtualhost `/usr/share/doc/flamejam/apache-vhost.conf`.
5.  Initialize the database using either test data or an admin account. For this, you can use
    either of the provided scripts in `/srv/flamejam/scripts/init-db.py` or
    `/srv/flamejam/scripts/seed-db.py`.

Development
-----------
For development and testing, firstly set up a virtualenv containing all dependencies. For your
convenience, a Makefile target has been provided. Run `make setup` to have it set up for you.

When this is done, run `python runserver.py` inside the virtualenv to fire up the
debug server and navigate to http://localhost:5000. Alternatively you can use `make run`.

Support and contact
-------------------
In order to receive help in getting this application to run, it would be best to ask
in the official IRC channel: #bacongamejam on irc.freenode.net.

You might as well report bugs on the Github project and we will surely come back to you.

Pull request are rather welcome.

License
-------
This application, all of its sources and resources are licensed under the zlib license with the
following exceptions:

 - jquery
 - lightbox
 - bootstrap

These exceptions are subject to their own copyrights and licenses. This project only makes use of them.

For the full license text, please see the included LICENSE file.
