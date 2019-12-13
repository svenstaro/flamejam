flamejam - a game jam application using Flask
=============================================

Description
-----------
flamejam is a generic game jam application that uses the Flask microframework.
It was initially created as a voting platforms for the [BaconGameJam](http://www.reddit.com/r/BaconGameJam).
However, it is generic and as such it is usable for any other game jam event.

This application is designed to make sure that participants vote on other
entries fairly and evenly.

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
    the provided Makefile option `setup`:

        $ make USERNAME=<username> PASSWORD=<password> EMAIL=<email> setup
        
    This will create an initial database setup with an admin user.
    As an alternative you can also call the commands yourself
    
        $ python3 -m venv venv
        $ venv/bin/flask init-db <username> <password> <email>
        $ venv/bin/flask seed-db
        
    `seed-db` supports an additional command line option `--flood` to setup 1000 dummy users


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


Run with docker
---------------
Flamejam comes with a prepared Dockerfile in order to run it as a container on your system.
Running flamejam with docker saves you installing all the required dependencies and encapsulates it inside a contained system.

To build the image you need to run as a container you call

    docker build --tag flamejam-image .
    
where `flamejam-image` can be freely chosen to name the image. You need to remember it in order to select it for the container.
Building the container concludes with

    Successfully built 6370906318a8
    Successfully tagged flamejam-image:latest

By running `docker images` you can see the built image.

    REPOSITORY          TAG                 IMAGE ID            CREATED             SIZE
    flamejam-image      latest              6370906318a8        24 seconds ago      156MB
    alpine              3.6                 43773d1dba76        9 months ago        4.03MB

Now you can start the container

    docker run --name flamejam flamejam-image
    
and it is up and running. Executing `docker ps` confirms your running container.

    CONTAINER ID        IMAGE               COMMAND                  CREATED             STATUS              PORTS               NAMES
    16e378d4c10f        flamejam-image      "uwsgi deploy/uwsgi.…"   32 seconds ago      Up 31 seconds       8080/tcp            flamejam
    
In order to continue with setting up flamejam you can login to the system by typing

    docker exec -it flamejam sh

Run with docker-compose
-----------------------
If you don't like the manual docker running or don't care about configuration options, you can install and use `docker-compose` instead.

    docker-compose up --build
    
This uses the provided `docker-compose.yml` configuration. Afterwards you can reach the server in the same way as described above.
Enter http://localhost:8080 to access the frontpage of the application