import random

from helpers.xmlbuilder import XMLBuilder


class Player:
    def __init__(self, user, name, team):
        self.name = name
        self.team = team
        self.user = user
        if user:
            self.server = user.server
            self.room = user.room

        self.ready = False
        self.dead = True

        self.hp = 40
        self.mp = 10
        self.yen = 20

        self.disease = None
        self.harms = list()

        self.deal = list()

        self.magics = list()
        self.items = list()
        self.resetItems()

    def __str__(self):
        return "<Player {name}>".format(name=self.name)

    def diseaseEffect(self):
        if self.disease:
            damage = 0
            if self.disease == "COLD":
                damage = 1
            elif self.disease == "FEVER":
                damage = 2
            elif self.disease == "HELL":
                damage = 5
            elif self.disease == "HEAVEN":
                damage = -5
            self.hp = max(0, min(99, self.hp - damage))

    def addHarm(self, harm):
        diseases = ["COLD", "FEVER", "HELL", "HEAVEN"]
        if harm in diseases:
            if self.disease:
                if self.disease == "HEAVEN":
                    self.hp = 0
                else:
                    idx = diseases.index(self.disease)
                    if idx < diseases.index(harm):
                        self.disease = harm
                    else:
                        self.disease = diseases[idx + 1]
            else:
                self.disease = harm
        else:
            if not harm in self.harms:
                self.harms.append(harm)
        print "Current Harm:", self.harms, "Current Disease:", self.disease

    def removeAllHarms(self, onlyLower=False):
        if not onlyLower:
            print "Remove all harms"
            self.disease = None
            self.harms = list()
            return

        print "Remove lower harms"
        if self.disease == "COLD" or self.disease == "FEVER":
            self.disease = None
        if "FOG" in self.harms:
            self.harms.remove("FOG")
        if "GLORY" in self.harms:
            self.harms.remove("GLORY")

    def resetItems(self):
        self.items = list()

    def dealItem(self, id, fromBuy=False):
        print self.name + " deal " + str(id)
        self.items.append(id)

        if not fromBuy and self.user is not None:
            builder = XMLBuilder("DEAL")
            builder.item(str(id))
            self.user.sendXml(builder)

    def hasItem(self, id):
        return id in self.items

    def getRandomItem(self):
        if len(self.items) == 0:
            return 0  # TODO: I don't know what is supposed to happen in this situation

        item = None
        while item is None:
            item = random.choice(self.items)
            if item in self.magics:
                item = None

        return item

    def discardItem(self, id):
        if self.hasItem(id):
            self.items.remove(id)
            return True
        return False

    def itemUsed(self, id):
        #TODO: Cost mp, etc etc etc
        if not self.hasItem(id):
            print self.name, "tried to use an item that don't have"
            return False
        
        item = self.server.itemManager.getItem(id)
        if item.type == "FIXED":
            return True

        if item.type == "MAGIC":
            if self.mp >= item.subValue:
                self.magics.append(item)
                self.mp -= item.subValue
                return True
            else:
                return False
        
        self.discardItem(id)
        return True
