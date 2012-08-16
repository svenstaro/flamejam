#
# This is a short script to kill all tables and fill them with new test data.
# It should be run from a virtualenv.
#

from flamejam import db
from flamejam.models import Announcement, Participant, Jam, Entry, Rating, Comment, EntryScreenshot
from datetime import datetime, timedelta

# Kill everything and recreate tables
db.drop_all()
db.create_all()

# Make users
peter = Participant("peter", "omgdlaad21", "roflomg-peter@mailinator.com")
paul = Participant("paul", "lol", "roflomg-paul@mailinator.com", is_admin=True, is_verified=True)
per = Participant("per", "lpdla", "roflomg-per@mailinator.com", is_verified = True, receive_emails = False)
pablo = Participant("pablo", "lad112", "roflomg-pablo@mailinator.com")
paddy = Participant("paddy", "rqtjio4j1", "roflomg-paddy@mailinator.com")

# Add users
db.session.add(peter)
db.session.add(paul)
db.session.add(per)
db.session.add(pablo)
db.session.add(paddy)

# Make jams
rgj1 = Jam("Reddit Game Jam 1", paul, datetime.utcnow() - timedelta(days=30))
rgj2 = Jam("Reddit Game Jam 2", pablo, datetime.utcnow() - timedelta(days=2))
rgj3 = Jam("Reddit Game Jam 3", peter, datetime.utcnow())
loljam = Jam("Loljam", paul, datetime.utcnow() - timedelta(days=3))
rgj4 = Jam("Reddit Game Jam 4", peter, datetime.utcnow() + timedelta(days=14))
rgj3.theme = "Zombies"

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

game3.team.append(paddy)
game3.team.append(pablo)
game3.team.append(peter)
game3.team.append(per)

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

# Add screenshots
s1 = EntryScreenshot("http://2.bp.blogspot.com/_gx7OZdt7Uhs/SwwanX_-API/AAAAAAAADAM/vbZbIPERdhs/s1600/Star-Wars-Wallpaper-star-wars-6363340-1024-768.jpg", "Awesome cover art", space_game)
s2 = EntryScreenshot("http://celebritywonder.ugo.com/wp/Hayden_Christensen_in_Star_Wars:_Episode_III_-_Revenge_of_the_Sith_Wallpaper_1_1280.jpg", "Close combat during final showdown", space_game)
s3 = EntryScreenshot("http://www.new-dream.de/image/wallpaper/film/star-wars/star-wars-03.jpg", "Nice open-space battle", space_game)
s4 = EntryScreenshot("http://wallpapercavern.com/wallpapers/wallpaper_lego_star_wars_the_video_game_01_1600-1280x960.jpg", "Example collection figure, shipped with premium DVD kit", space_game)
s5 = EntryScreenshot("http://images.psxextreme.com/wallpapers/ps3/star_wars___battle_1182.jpg", "Sample vehicles", space_game)
s6 = EntryScreenshot("http://sethspopcorn.com/wp-content/uploads/2010/10/CloneTrooper.jpg", "Character selection screen", space_game)

db.session.add(s1)
db.session.add(s2)
db.session.add(s3)
db.session.add(s4)
db.session.add(s5)
db.session.add(s6)

# Make ratings
rating1 = Rating(3, 5, 1, 7, 3, 1, 5, 7, 2, "cool stuff", best_game, peter)
rating2 = Rating(10, 6, 1, 7, 6, 10, 10, 1, 10, "adasdff", best_game, paul)
rating3 = Rating(3, 5, 1, 5, 2, 2, 10, 3, 3, "cadkak", space_game, paul)
rating4 = Rating(9, 5, 6, 7, 3, 1, 1, 3, 6, "fakpdak1", clone, paul)
rating5 = Rating(3, 5, 8, 5, 3, 6, 4, 8, 1, "madkm1njn", clone, paddy)
rating6 = Rating(3, 5, 8, 5, 3, 6, 4, 5, 2, "madkm1njn", game1, paddy)
rating7 = Rating(3, 5, 8, 5, 3, 6, 9, 1, 2, "madkm1njn", game2, paddy)
rating8 = Rating(3, 5, 8, 5, 3, 6, 2, 2, 3, "madkm1njn", game2, peter)
rating9 = Rating(2, 1, 3, 9, 8, 4, 5, 3, 2, "cool stuff 2", game2, paul)

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
