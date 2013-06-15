default: run

setup:
	virtualenv2 -p python2 env && . env/bin/activate && \
		pip install -i http://c.pypi.python.org/simple/ --upgrade \
			flask flask-mail flask-sqlalchemy flask-wtf \
			flask-login flask-markdown python-dateutil \
			scrypt requests alembic flask-principal mysql-python \
			flask-cache

run:
	. env/bin/activate && python2 runserver.py

init-db:
	. env/bin/activate && python2 scripts/init-db.py

seed-db:
	. env/bin/activate && python2 scripts/seed-db.py

install:
	mkdir -p $(DESTDIR)/srv/flamejam
	cp -r alembic flamejam scripts $(DESTDIR)/srv/flamejam
	cp alembic.ini flamejam.wsgi runserver.py Makefile $(DESTDIR)/srv/flamejam/
	
	mkdir -p $(DESTDIR)/etc/flamejam
	
	mkdir -p $(DESTDIR)/usr/share/doc/flamejam
	cp -r doc/* $(DESTDIR)/usr/share/doc/flamejam/
	cp LICENSE README.md $(DESTDIR)/usr/share/doc/flamejam/
	
	cd $(DESTDIR)/srv/flamejam && make setup

uninstall:
	rm -r $(DESTDIR)/srv/flamejam
	rm -r $(DESTDIR)/etc/flamejam
	rm -r $(DESTDIR)/usr/share/doc/flamejam
