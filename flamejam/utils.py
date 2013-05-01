from flamejam import app
import random
import scrypt
import requests
import re

def average(list):
    return sum(list) / float(len(list)) if len(list) else 0

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

def randstr(length):
    return ''.join(chr(random.randint(0,255)) for i in range(length))

def hash_password(password, maxtime=5, datalength=256):
    salt = randstr(datalength)
    hashed_password = scrypt.encrypt(salt, str(password), maxtime=maxtime)
    return bytearray(hashed_password)

def verify_password(hashed_password, guessed_password, maxtime=300):
    try:
        scrypt.decrypt(str(hashed_password), str(guessed_password), maxtime)
        return True
    except scrypt.error as e:
        print "scrypt error: %s" % e    # Not fatal but a necessary measure if server is under heavy load
        return False

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
