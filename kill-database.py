#
# This is a short script to kill all tables and fill them with new test data.
# It should be run from a virtualenv.
#

from flamejam import db
from flamejam.models import Announcement, Participant, Jam, Entry, Rating, Comment
from datetime import datetime, timedelta

# Kill everything and recreate tables
db.drop_all()
db.create_all()

# Make users
peter = Participant("peter", "omgdlaad21", "peter@rofl.com")
paul = Participant("paul", "lol", "paul@rofl.com", is_admin=True,
        is_verified=True)
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
game1 = Entry("game1", "game1", loljam, paul)
game2 = Entry("game2", "game2", loljam, paddy)
game3 = Entry("game3", "game3", loljam, pablo)
game4 = Entry("game4", "game4", loljam, peter)

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
db.session.add(game1)
db.session.add(game2)
db.session.add(game3)
db.session.add(game4)

# Make ratings
rating1 = Rating(3, 5, 1, 7, 3, 1, "cool stuff", best_game, peter)
rating2 = Rating(10, 6, 1, 7, 6, 10, "adasdff", best_game, paul)
rating3 = Rating(3, 5, 1, 5, 2, 2, "cadkak", space_game, paul)
rating4 = Rating(9, 5, 6, 7, 3, 1, "fakpdak1", clone, paul)
rating5 = Rating(3, 5, 8, 5, 3, 6, "madkm1njn", clone, paddy)
rating6 = Rating(3, 5, 8, 5, 3, 6, "madkm1njn", game1, paddy)
rating7 = Rating(3, 5, 8, 5, 3, 6, "madkm1njn", game2, paddy)
rating8 = Rating(3, 5, 8, 5, 3, 6, "madkm1njn", game2, peter)

# Add ratings
db.session.add(rating1)
db.session.add(rating2)
db.session.add(rating3)
db.session.add(rating4)
db.session.add(rating5)
db.session.add(rating6)
db.session.add(rating7)
db.session.add(rating8)

# Make comments
comment1 = Comment("lol so bad", best_game, peter)
comment2 = Comment("the worst", best_game, paul)
comment3 = Comment("pew pew pew", space_game, paul)
comment4 = Comment("omg clone", clone, paul)
comment5 = Comment("pong is better", clone, paddy)

# Add comments
db.session.add(comment1)
db.session.add(comment2)
db.session.add(comment3)
db.session.add(comment4)
db.session.add(comment5)

# Make announcements
ann1 = Announcement("New game jam now.")
ann2 = Announcement("Game jam is over.")
ann3 = Announcement("Voting is over.")
ann4 = Announcement("New game jam announced.")
ann5 = Announcement("Game jam started.")

# Add announcements

db.session.add(ann1)
db.session.add(ann2)
db.session.add(ann3)
db.session.add(ann4)
db.session.add(ann5)

# Commmit it all
db.session.commit()
