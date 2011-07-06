from flask import Flask
from datetime import *
from flaskext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flamejam.db'
app.config['SQLALCHEMY_ECHO'] = True
app.config['SECRET_KEY'] = 'lolsecret'
db = SQLAlchemy(app)
    
#define filters
@app.template_filter()
def formattime(s):
	return s.strftime("%Y-%m-%d %H:%M:%S")
	
#@app.template_filter()
#def startwith(s, start):
#	return s.startswith(start)
	
@app.template_filter()
def humantime(s):
	diff = datetime.utcnow() - s
	if(diff.seconds < 10):
		return "just now"
	elif(diff.seconds < 60):
		return str(diff.seconds) + " second" + ("s" if diff.seconds > 1 else "") + " ago"
	mins = (diff.seconds - diff.seconds % 60) / 60
	if(mins < 60):
		return str(mins) + " minute" + ("s" if mins > 1 else "") + " ago"
	hours = (mins - mins % 60) / 60
	if(hours < 24):
		return str(hours) + " hour" + ("s" if hours > 1 else "") + " ago"
	if(diff.days < 14):
		return str(diff.days) + " day" + ("s" if diff.days > 1 else "") + " ago"
	weeks = (diff.days - diff.days % 7) / 7
	if(weeks <= 4):
		return str(weeks) + " week" + ("s" if weeks > 1 else "") + " ago"
	return formattime(s)

import flamejam.views
import flamejam.models

@app.context_processor
def inject_announcement():
	a = flamejam.models.Announcement.query.order_by(flamejam.models.Announcement.posted.desc()).first()	
	return dict(last_announcement = a)
