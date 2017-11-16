default: run

.PHONY: run
run: venv
	FLASK_APP=app.py venv/bin/flask run

.PHONY: venv
venv:
	python3 -m venv venv
	venv/bin/pip install --upgrade pip
	venv/bin/pip install -r requirements.txt -r dev-requirements.txt --upgrade

.PHONY: clean
clean:
	rm -rf venv
