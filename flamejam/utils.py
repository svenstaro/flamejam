from flamejam import app
import requests
import re
from hashlib import sha512

def get_slug(s):
    s = s.lower()
    s = re.sub(r"[\s_+]+", "-", s)
    s = re.sub("[^a-z0-9\-]", "", s)
    s = re.sub("-+", "-", s)
    return s

def findLocation(loc):
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

def hashPassword(pw):
    return sha512((pw + app.config['SECRET_KEY']).encode('utf-8')).hexdigest()

def get_current_jam():
    from flamejam.models import Jam, JamStatusCode
    for jam in Jam.query.all():
        if jam.getStatus().code == JamStatusCode.RUNNING:
            return jam
    return None
