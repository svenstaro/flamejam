default: run

setup:
	virtualenv -p python2 env && . env/bin/activate && \
		pip install --upgrade flask flask-mail flask-sqlalchemy flask-wtf \
									flask-login flask-markdown python-dateutil \
									scrypt requests alembic flask-principal

run:
	. env/bin/activate && python2 runserver.py

kill:
	. env/bin/activate && python2 kill-database.py
