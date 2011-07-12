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

def _absdelta(d):
    if d.seconds < 0 or d.minutes < 0 or d.hours < 0 or d.days < 0 or d.months < 0 or d.years < 0:
        return -d
    return d

# format a timedelta in human-readable format (e.g. "in 20 minutes" or "3 weeks ago")
@app.template_filter()
def humandelta(s, other = None):
    if other:
        # we got 2 datetimes
        return _delta(_absdelta(timedelta(other, s))).strip()


    if s.seconds < 0 or s.minutes < 0 or s.hours < 0 or s.days < 0 or s.months < 0 or s.years < 0:
        return "%s ago" % _delta(-s).strip()
    elif s.seconds > 0 or s.minutes > 0 or s.hours > 0 or s.days > 0 or s.months > 0 or s.years > 0:
        return "in %s" % _delta(s).strip()
    else:
        return s

@app.template_filter()
def humantime(s):
    diff = timedelta(s, datetime.utcnow())
    if diff.years < 1:
        return humandelta(diff)
    else:
        return formattime(s)
