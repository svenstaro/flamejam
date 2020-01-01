flamejam - a game jam application using Flask
=============================================

[![Docker Cloud Build Status](https://img.shields.io/docker/cloud/build/svenstaro/flamejam)](https://hub.docker.com/r/svenstaro/flamejam)
[![license](http://img.shields.io/badge/license-zlib-blue.svg)](https://github.com/svenstaro/flamejam/blob/master/LICENSE)
[![Stars](https://img.shields.io/github/stars/svenstaro/flamejam.svg)](https://github.com/svenstaro/flamejam/stargazers)

Description
-----------
flamejam is a generic game jam application implemented in Python and using the
Flask microframework.
It was initially created as a voting platforms for the [BaconGameJam](http://www.reddit.com/r/BaconGameJam).
However, it is generic and as such it is usable for any other game jam event.

This application is designed to make sure that participants vote on other
entries fairly and evenly.

How to run for development
--------------------------
You are currently expected to run some kind of POSIX system such as Linux. This software has
not been tested on Windows and it would be quite a wonder indeed if it worked there.

1.  Copy the default config from `doc/flamejam.cfg.default` to `flamejam.cfg`
    and configure it to your needs.
2.  Initialize the database using either test data or an admin account.

    Example for an empty database with just an admin account called `peter` and password `hunter2`:

        poetry run flask init-db peter hunter2 peter@example.com

    Example to seed a database with test data:

        poetry run flask seed-db
3.  Then, running the application should be as simple as calling

        make run_debug

How to run in production
------------------------
Docker is the primary supported way to run this software in production. It can
easily be run without Docker but it's very hard for me to universally support
that so if you don't want to use Docker, you should adopt the following
instructions to your own systems. Follow step 1. and 2. from above. Then, run

    docker run -v $PWD/flamejam.cfg:/etc/flamejam/flamejam.cfg -p 8080:8080 svenstaro/flamejam:latest

Support and contact
-------------------
In order to receive help in getting this application to run, it would be best
to ask here on GitHub via the issues system.

Pull requests are welcome.

License
-------
This application, all of its sources and resources are licensed under the zlib license with the
following exceptions:

 - jquery
 - lightbox
 - bootstrap

These exceptions are subject to their own copyrights and licenses. This project only makes use of them.

For the full license text, please see the included LICENSE file.
