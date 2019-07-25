

class Item:
    def __init__(self):
        #self.assistantType = str()
        self.id = int()
        self.type = str()
        self.attackKind = str()
        self.attackExtra = str()
        self.defenseKind = str()
        self.defenseExtra = str()
        self.attribute = str()
        self.value = int()
        self.subValue = int()
        self.hitRate = int()
        self.price = int()
        self.weight = int()

        #WEAPON,ATK,DYING_ATTACK,,,LIGHT,1,30,75,10,1
        #Arco /\

    def __repr__(self):
        return "<Item {id} \"{dict}\">".format(id=self.id, dict=self.__dict__)

    def isAtkHarm(self):
        return self.attackExtra in ["COLD", "FEVER", "HELL", "HEAVEN", "FOG", "ILLUSION", "GLORY", "DARK_CLOUD"]

    def isDefHarm(self):
        return self.defenseExtra in ["COLD", "FEVER", "HELL", "HEAVEN", "FOG", "ILLUSION", "GLORY", "DARK_CLOUD"]

    def loadFromData(self, data):
        #self.assistantType = None
        self.type = data[0]
        self.attackKind = data[1]
        self.attackExtra = data[2]
        self.defenseKind = data[3]
        self.defenseExtra = data[4]
        self.attribute = data[5]
        self.value = int(data[6]) if data[6] != "" else 0
        self.subValue = int(data[7]) if data[7] != "" else 0
        self.hitRate = int(data[8]) if data[8] != "" else 0
        self.price = int(data[9]) if data[9] != "" else 0
        self.weight = int(data[10]) if data[10] != "" else 0

        # print(repr(self))

    def getAD(self):
        attack = 0
        defense = 0
        if self.attackKind == "ATK" and self.defenseKind == "DFS":
            attack = self.value
            defense = self.subValue
        elif self.attackKind == "ATK" and not self.defenseKind:
            attack = self.value
        elif not self.attackKind and self.defenseKind == "DFS":
            defense = self.value
        else:
            print "Unknown item AD!?"
            print self.attackKind, self.defenseKind
        return [attack, defense]
