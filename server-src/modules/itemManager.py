from modules.item import Item
import numpy
import random

class ItemManager:
    def __init__(self, dataFilename):
        self.items = list()
        self.itemsProbabilities = list()

        self.loadItems(dataFilename)

    def loadItems(self, dataFilename):
        with open(dataFilename, 'r') as f:
            for line in f:
                item = Item()
                item.id = len(self.items)
                item.loadFromData(line.rstrip("\n").split(","))
                self.items.append(item)
                self.itemsProbabilities.append(item.weight)

        self.itemsProbabilities = numpy.array(map(float, self.itemsProbabilities))/10
        self.itemsProbabilities = self.itemsProbabilities/sum(self.itemsProbabilities)
        
        print "ItemManager: Loaded %d items" % len(self.items)

    def getRandomItem(self, types):
        item = None
        while item is None:
            chosen = self.items[random.randrange(len(self.items))]
            item = chosen if chosen.type in types else None
        return item

    def getProbRandomItems(self, count):
        return numpy.random.choice(self.items, count, p=self.itemsProbabilities)

    def getItem(self, id):
        for item in self.items:
            if item.id == id:
                return item
        return None
