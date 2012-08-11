default: run

setup:
	./setup.sh

run:
	./run.sh

kill:
	. env/bin/activate && python2 kill-database.py
