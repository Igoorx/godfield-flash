from modules.item import Item
#import numpy
import random
import secrets
import bisect

class ItemManager:
    def __init__(self, dataFilename):
        self.items = list()
        self.itemsWeights = list()
        self.totalWeight = int()
        self.cumWeights = list()
        self.randGen = secrets.SystemRandom()

        self.loadItems(dataFilename)

    def loadItems(self, dataFilename):
        with open(dataFilename, 'r') as f:
            for line in f:
                item = Item()
                item.id = len(self.items)
                item.loadFromData(line.rstrip("\n").split(","))
                self.items.append(item)
                self.itemsWeights.append(item.weight)

        #self.itemsProbabilities = numpy.array(map(float, self.itemsProbabilities))
        #self.itemsProbabilities = self.itemsProbabilities/sum(self.itemsProbabilities)
        
        self.buildCumWeights()

        print "ItemManager: Loaded %d items" % len(self.items)

    def buildCumWeights(self):
        self.totalWeight = 0
        self.cumWeights = []
        for w in self.itemsWeights:
            self.totalWeight += w
            self.cumWeights.append(self.totalWeight)

    def getRandomItem(self, types):
        item = None
        while item is None:
            chosen = self.items[random.randrange(len(self.items))]
            item = chosen if chosen.type in types else None
        return item

    def getProbRandomItems(self, count):
        ret = []
        for _ in range(count):
            x = self.randGen.random() * self.totalWeight
            i = bisect.bisect(self.cumWeights, x)
            ret.append(self.items[i])
        return ret
        #return numpy.random.choice(self.items, count, p=self.itemsProbabilities)

    def getItem(self, id):
        for item in self.items:
            if item.id == id:
                return item
        return None
