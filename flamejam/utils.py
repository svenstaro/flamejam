from flamejam import app
import requests
import re
from hashlib import sha512

def average(list):
    return sum(list) / float(len(list))

def average_non_zero(list):
    list = [x for x in list if x != 0]
    return average(list)

def get_slug(s):
    s = s.lower()
    s = re.sub(r"[\s_+]+", "-", s)
    s = re.sub("[^a-z0-9\-]", "", s)
    s = re.sub("-+", "-", s)
    return s

def findLocation(loc):
    try:
        r = requests.get("http://maps.googleapis.com/maps/api/geocode/json?address=%s&sensor=false&language=en" % loc)
        c = r.json()["results"][0]
        a = c["address_components"]

        city = ""
        state = ""
        region = ""
        flag = ""
        coords = "%s,%s" % (c["geometry"]["location"]["lat"], c["geometry"]["location"]["lng"])

        for comp in a:
            if comp["types"][0] == "locality": city = comp["long_name"]
            elif comp["types"][0] == "administrative_area_level_1": region = comp["long_name"]
            elif comp["types"][0] == "country":
                state = comp["long_name"]
                flag = comp["short_name"].lower()

        first = state

        if state == "United States" and region:
            first += ", " + region

        if city:
            first += ", " + city
        return first, coords, flag
    except:
        return None, None, None

def hashPassword(pw):
    return sha512((pw + app.config['SECRET_KEY']).encode('utf-8')).hexdigest()

def get_current_jam():
    from flamejam.models import Jam, JamStatusCode
    next = None
    previous = None
    for jam in Jam.query.all():
        if jam.getStatus().code == JamStatusCode.RUNNING:
            return jam
        elif jam.getStatus().code <= JamStatusCode.RUNNING:
            if not next or next.start_time > jam.start_time:
                next = jam
        else:
            if not previous or previous.end_time < jam.end_time:
                previous = jam

    return next or previous
