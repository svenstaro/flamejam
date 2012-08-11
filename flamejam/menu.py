from flamejam import app
from flask import url_for

# this is the decorator (it is used like a function, thus the lower case name
class path(object):
    def __init__(self, *args):
        self.path = args

    def __call__(self, function):
        m = root_menu
        for p in self.path:
            if p in m.children:
                m = m.children[p]
            else:
                m = MenuEntry(p, m)
        m.functions.append(function)
        return function

class MenuEntry(object):
    def __init__(self, name, parent):
        self.name = name
        self.functions = []
        self.children = {}
        self.parent = parent
        if parent:
            parent.children[name] = self

    def findPathOfFunction(self, function):
        for f in self.functions:
            if f == function or f.__name__ == function:
                return self.fullPath

        for k in self.children:
            c = self.children[k]
            p = c.findPathOfFunction(function)
            if p: return p

        return None

    @property
    def fullPath(self):
        if self.parent:
            return self.parent.fullPath + [self]
        if self.name:
            return [self]
        return []

    @property
    def link(self):
        for f in self.functions:
            try:
                return url_for(f.__name__)
            except:
                pass
        return None

    def __repr__(self):
        return self.name

root_menu = MenuEntry("", None)

def getPath(endpoint):
    return root_menu.findPathOfFunction(endpoint)

def inPath(endpoint, name):
    for x in getPath(endpoint):
        if str(x) == name:
            return True
    return False

@app.context_processor
def injectPathStuff():
    return dict(getPath = getPath, inPath = inPath)


def printMenu(m = root_menu, indent = 0):
    for k in m.children:
        c = m.children[k]
        print "  " * indent + "- " + c.name
        printMenu(c, indent + 1)
