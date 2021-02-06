import random

from helpers.xmlbuilder import XMLBuilder


class Player:
    def __init__(self, user, name, team):
        self.name = name
        self.team = team
        self.user = user

        if user is not None:
            self.server = user.server
            self.room = user.room

        self.reset()

    def __str__(self):
        return "<Player {name}>".format(name=self.name)

    def hasLowerDisease(self):
        return self.disease in ["COLD", "FEVER", "FOG", "GLORY"]

    def reset(self):
        self.ready = bool()
        self.dead = False
        self.lost = False
        self.finished = False
        self.waitingAttackTurn = False

        self.hp = 40
        self.mp = 10
        self.yen = 20

        self.disease = None
        self.worseChance = int()
        self.harms = list()

        self.deal = 10

        self.magics = list()
        self.items = list()

    def diseaseEffect(self, selfAttack = False):
        if not self.disease or (not selfAttack and self.hp == 0):
            # Ignore if we aren't diseased or we are already dead
            assert False, "Invalid call to diseaseEffect"
            return False
        
        damage = 0
        if self.disease == "COLD":
            damage = 1
        elif self.disease == "FEVER":
            damage = 2
        elif self.disease == "HELL":
            damage = 5
        elif self.disease == "HEAVEN":
            damage = -5
        else:
            assert False, "Unimplemented disease: " + self.disease
        
        self.hp = max(0, min(99, self.hp - damage))
        return True

    def addHarm(self, harm):
        diseases = ["COLD", "FEVER", "HELL", "HEAVEN"]
        if harm in diseases:
            if self.disease:
                if self.disease == "HEAVEN":
                    print "FALL FROM THE HEAVEN"
                    self.hp = 0
                else:
                    idx = diseases.index(self.disease)
                    if idx < diseases.index(harm):
                        self.disease = harm
                    else:
                        self.disease = diseases[idx + 1]
            else:
                self.disease = harm
            self.worseChance = 0
        else:
            if not harm in self.harms:
                self.harms.append(harm)
        print "Current Harm:", self.harms, "Current Disease:", self.disease

    def removeAllHarms(self, onlyLower=False):
        if not onlyLower:
            print "Remove all harms"
            self.disease = None
            self.worseChance = 0
            self.harms = list()
            return

        print "Remove lower harms"
        if self.disease == "COLD" or self.disease == "FEVER":
            self.disease = None
            self.worseChance = 0
        if "FOG" in self.harms:
            self.harms.remove("FOG")
        if "GLORY" in self.harms:
            self.harms.remove("GLORY")

    def dealItem(self, id, fromBuy=False):
        print self.name + " deal " + str(id)
        self.items.append(int(id))

        if not fromBuy and self.user is not None:
            builder = XMLBuilder("DEAL")
            builder.item(str(id))
            self.user.sendXml(builder)

    def hasItem(self, id):
        return id in self.items

    def hasAttackKind(self, kind):
        for id in self.items:
            item = self.server.itemManager.getItem(id)
            if item.attackKind == kind:
                return True
        return False

    def hasMagic(self, id):
        return id in self.magics

    def getRandomItem(self):
        if len(self.items) == 0:
            return 0

        return random.choice(self.items)

    def getRandomMagic(self):
        if len(self.magics) == 0:
            return 0
        
        return random.choice(self.magics)

    def discardItem(self, id):
        if self.hasItem(id):
            self.items.remove(id)
            return True
        assert False, "Tried to discard non-existent item"
        return False

    def discardMagic(self, id):
        if self.hasMagic(id):
            self.magics.remove(id)
            return True
        assert False, "Tried to discard non-existent magic"
        return False

    def itemUsed(self, id, noMPCost):
        #TODO: Cost mp, etc etc etc
        if not self.hasItem(id):
            assert False, "Tried to use an item that he doesn't have"
            return False
        
        item = self.server.itemManager.getItem(id)
        if item.type == "FIXED":
            return True

        if item.type == "MAGIC":
            if noMPCost or self.mp >= item.subValue:
                # Register and use magic
                self.magics.append(id)
                self.items.remove(id)
                if not noMPCost:
                    self.mp -= item.subValue
                return True
            else:
                print(self.mp)
                print(item.__dict__)
                assert False, "Tried to use magic with not enough MP"
                return False
        
        self.items.remove(id)
        return True

    def magicUsed(self, id, noMPCost):
        #TODO: Cost mp, etc etc etc
        if not self.hasMagic(id):
            return False
        
        item = self.server.itemManager.getItem(id)

        if noMPCost or self.mp >= item.subValue:
            if not noMPCost:
                self.mp -= item.subValue
            return True
        
        assert False, "Tried to use magic with not enough MP"
        return False
