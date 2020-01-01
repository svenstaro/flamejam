default: run_dev

.PHONY: install
install:
	poetry install

.PHONY: run_dev
run_dev: install
	poetry run uwsgi uwsgi_dev.ini

.PHONY: run_prod
run_prod: install
	poetry run uwsgi uwsgi_prod.ini
