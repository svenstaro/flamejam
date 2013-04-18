# -*- coding: utf-8 -*-

from flamejam import app, db
from flask import Markup

PACKAGE_TYPES = {
    "web":           ("Web link (Flash etc.)", "Web"),
    "linux":         ("Binaries: Linux 32/64-bit", "Linux"),
    "linux32":       ("Binaries: Linux 32-bit", "Linux32"),
    "linux64":       ("Binaries: Linux 64-bit", "Linux64"),
    "windows":       ("Binaries: Windows", "Windows"),
    "windows64":     ("Binaries: Windows 64-bit", "Windows64"),
    "mac":           ("Binaries: MacOS Application", "MacOS"),
    "source":        ("Source: package", "Source"),
    "git":           ("Source: Git repository", "git"),
    "svn":           ("Source: SVN repository", "svn"),
    "hg":            ("Source: HG repository", "hg"),
    "combi":         ("Combined package: Linux + Windows + Source (+ more, optional)", "Combined"),
    "love":          ("Love package", ".love"),
    "blender":       ("Blender file", ".blend"),
    "unknown":       ("Other", "other")
}

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

    def getLinkShort(self):
        return Markup('<a href="%s">%s</a>' % (self.url, GamePackage.typeStringShort(self.type)))

    def __repr__(self):
        return "<GamePackage %r>" % self.id

    @staticmethod
    def typeString(type):
        if type in PACKAGE_TYPES:
            return PACKAGE_TYPES[type][0]
        return "Unknown"

    @staticmethod
    def typeStringShort(type):
        if type in PACKAGE_TYPES:
            return PACKAGE_TYPES[type][1]
        return "Unknown"

    @staticmethod
    def compare(left, right):
        x = right.getTotalScore() - left.getTotalScore()
        if x > 0:
            return 1
        elif x < 0:
            return -1
        else:
            return 0

