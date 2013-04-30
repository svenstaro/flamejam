default: run

setup:
	virtualenv -p python2 env && . env/bin/activate && \
		pip install -i http://c.pypi.python.org/simple/ --upgrade \
			flask flask-mail flask-sqlalchemy flask-wtf \
			flask-login flask-markdown python-dateutil \
			scrypt requests alembic flask-principal mysql-python

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
	
	install -Dm600 doc/flamejam.cfg.default $(DESTDIR)/etc/flamejam/flamejam.cfg.default
	
	mkdir -p $(DESTDIR)/usr/share/doc/
	cp -r doc $(DESTDIR)/usr/share/doc/flamejam
	cp LICENSE README.md $(DESTDIR)/usr/share/doc/flamejam/
	
	cd $(DESTDIR)/srv/flamejam && make setup

uninstall:
	rm -r $(DESTDIR)/srv/flamejam
	rm -r $(DESTDIR)/etc/flamejam
	rm -r $(DESTDIR)/usr/share/doc/flamejam
