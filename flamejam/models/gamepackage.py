# -*- coding: utf-8 -*-

from flamejam import app, db
from flask import Markup

class GamePackage(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    url = db.Column(db.String(256))
    game_id = db.Column(db.Integer, db.ForeignKey("game.id"))
    type = db.Column(db.Enum(
        "web",      # Flash, html5, js...
        "linux",    # Linux binaries (e.g. *.tar.gz)
        "linux32",  # Linux32 binaries (e.g. *.tar.gz)
        "linux64",  # Linux64 binaries (e.g. *.tar.gz)
        "windows",  # Windows binaries (e.g. *.zip, *.exe)
        "windows64",# Windows64 binaries (e.g. *.zip, *.exe)
        "mac",      # MacOS application packages
        "combi",    # Linux + Windows + Source (and more, optional)
        "love",     # Löve packages
        "blender",  # Blender save file (*.blend)
        "source",   # Source package (e.g. *.zip or *.tar.gz)
        "git",      # Version control repository: GIT
        "svn",      # Version control repository: SVN
        "hg",       # Version control repository: HG
        "unknown"))

    def __init__(self, game, url, type = "unknown"):
        self.url = url
        self.type = type
        self.game = game

    def getLink(self):
        return Markup('<a href="%s">%s</a>' % (self.url, GamePackage.typeString(self.type)))

    def __repr__(self):
        return "<GamePackage %r>" % self.id

    def typeString(self):
        return Game.typeString(self.type)

    @staticmethod
    def typeString(type):
        if type == "web":           return "Web link (Flash etc.)"
        if type == "linux":         return "Binaries: Linux 32/64-bit"
        if type == "linux32":       return "Binaries: Linux 32-bit"
        if type == "linux64":       return "Binaries: Linux 64-bit"
        if type == "windows":       return "Binaries: Windows"
        if type == "windows64":     return "Binaries: Windows 64-bit"
        if type == "mac":           return "Binaries: MacOS Application"
        if type == "source":        return "Source: package"
        if type == "git":           return "Source: Git repository"
        if type == "svn":           return "Source: SVN repository"
        if type == "hg":            return "Source: HG repository"
        if type == "combi":         return "Combined package: Linux + Windows + Source (+ more, optional)"
        if type == "love":          return "Love package"
        if type == "blender":       return "Blender file"
        if type == "unknown":       return "Other"

        return "Unknown type"

    @staticmethod
    def compare(left, right):
        x = right.getTotalScore() - left.getTotalScore()
        if x > 0:
            return 1
        elif x < 0:
            return -1
        else:
            return 0

