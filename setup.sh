#!/bin/bash

virtualenv -p python2 env
. env/bin/activate
pip install flask
pip install flask-mail
pip install flask-sqlalchemy
pip install flask-wtf
pip install flask-login
pip install flask-markdown
pip install python-dateutil
