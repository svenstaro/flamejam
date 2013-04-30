#
# This is a short script to kill all tables and add a single admin, given as parameters.
# It should be run from a virtualenv.
#

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flamejam import db
from flamejam.models import User, Jam, Game, Rating, Comment, GameScreenshot
from datetime import datetime, timedelta

db.drop_all()
db.create_all()

if len(sys.argv) < 4 or len(sys.argv) >= 5 or \
        sys.argv[1] == "-h" or sys.argv[1] == "--help":
    print "Provide initial admin data using these parameters:"
    print sys.argv[0] + " <username> <password> <email>"
    exit(1)

username = sys.argv[1]
password = sys.argv[2]
email = sys.argv[3]

admin = User(username, password, email, is_admin = True, is_verified = True)
db.session.add(admin)

db.session.commit()
