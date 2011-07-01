#
# This is a short script to kill all tables and fill them with new test data.
# It should be run from a virtualenv.
#

from flamejam import db, Participant, Jam, Entry
from datetime import datetime, timedelta

# Kill everything and recreate tables
db.drop_all()
db.create_all()

# Make users
peter = Participant("peter", "omgdlaad21", "peter@rofl.com")
paul = Participant("paul", "dadadf", "paul@rofl.com")
per = Participant("per", "lpdla", "per@rofl.com")
pablo = Participant("pablo", "lad112", "pablo@rofl.com")
paddy = Participant("paddy", "rqtjio4j1", "paddy@rofl.com")

# Add users
db.session.add(peter)
db.session.add(paul)
db.session.add(per)
db.session.add(pablo)
db.session.add(paddy)

# Make jams
rgj1 = Jam("rgj1", "Reddit Game Jam 1", datetime.utcnow() - timedelta(days=30))
rgj2 = Jam("rgj2", "Reddit Game Jam 2", datetime.utcnow() - timedelta(days=2))
rgj3 = Jam("rgj3", "Reddit Game Jam 3", datetime.utcnow())
loljam = Jam("loljam", "Loljam", datetime.utcnow() - timedelta(days=3))
rgj4 = Jam("rgj4", "Reddit Game Jam 4", datetime.utcnow() + timedelta(days=14))

# Add jams
db.session.add(rgj1)
db.session.add(rgj2)
db.session.add(rgj3)
db.session.add(loljam)
db.session.add(rgj4)

# Make entries
best_game = Entry("best game", "Simply the best game", rgj1, peter)
space_game = Entry("space game", "A space shooter game", rgj1, paul)
clone = Entry("clone", "very original game", rgj2, paddy)
test_game = Entry("test_game", "just testing crap out", rgj2, paul)
nyan = Entry("nyan", "game with a cat", rgj3, peter)
derp = Entry("derp", "herp herp", rgj3, paul)
lorem = Entry("lorem", "ipsum dolor?", rgj3, pablo)
rtype = Entry("rtype", "some schmup game", rgj4, paddy)
tetris = Entry("tetris", "original concept", rgj4, paul)

# Add entries
db.session.add(best_game)
db.session.add(space_game)
db.session.add(clone)
db.session.add(test_game)
db.session.add(nyan)
db.session.add(derp)
db.session.add(lorem)
db.session.add(rtype)
db.session.add(tetris)

# Commmit it all
db.session.commit()
