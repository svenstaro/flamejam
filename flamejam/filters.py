from flamejam import app
from datetime import *
from dateutil import relativedelta


# format a timestamp in default format (0000-00-00 00:00:00)
@app.template_filter()
def formattime(s):
	return s.strftime("%Y-%m-%d %H:%M:%S")

def _s(n, s):
	if n == 0:
		return ""
	return str(n) + " " + s + ("s" if n > 1 else "")

def _delta(delta):
	if delta.years > 0:
		return _s(delta.years, "year") + " " + _s(delta.months, "month")
	if delta.months > 0:
		return _s(delta.months, "month") + " " + _s(delta.days, "day")
	if delta.days > 0:
		return _s(delta.days, "day") + " " + _s(delta.hours, "hour")
	if delta.hours > 0:
		return _s(delta.hours, "hour") + " " + _s(delta.minutes, "minute")
	if delta.minutes > 0:
		return _s(delta.minutes, "minute") + " " + _s(delta.seconds, "second")
	return _s(delta.seconds, "second")
		
def timedelta(starttime, endtime):
	return relativedelta.relativedelta(starttime, endtime)

# format a timedelta in human-readable format (e.g. "in 20 minutes" or "3 weeks ago")
@app.template_filter()
def humandelta(s, other = None):
	if other:
		# we got 2 datetimes
		return _delta(timedelta(other, s))
		 
	if s.seconds < 0: # in past
		return "%s ago" % _delta(-s)
	elif s.seconds > 0:
		return "in %s" % _delta(s)
	else:
		return s
	
@app.template_filter()
def humantime(s):
	diff = timedelta(s, datetime.utcnow())
	if diff.years < 1:
		return humandelta(diff)
	else:
		return formattime(s)
