#!/bin/bash

virtualenv -p python2 env
. env/bin/activate
pip install --upgrade flask flask-mail flask-sqlalchemy flask-wtf flask-login flask-markdown python-dateutil requests
