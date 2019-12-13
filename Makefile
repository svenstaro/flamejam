default: run

.PHONY: run
run: venv
	FLASK_APP=app.py FLASK_DEBUG=1 venv/bin/flask run

.PHONY: uwsgi_run
uwsgi_run: venv
	venv/bin/uwsgi deploy/uwsgi.ini

.PHONY: setup
setup: venv
	python3 -m venv venv
	venv/bin/flask init-db $(USERNAME) $(PASSWORD) $(EMAIL)
	venv/bin/flask seed-db

.PHONY: venv
venv:
	python3 -m venv venv
	venv/bin/pip install --upgrade pip
	venv/bin/pip install -r requirements.txt -r dev-requirements.txt --upgrade

.PHONY: clean
clean:
	rm -rf venv
