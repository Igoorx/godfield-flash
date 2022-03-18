from dataclasses import dataclass
import numpy
import random

__all__ = ("Item", "ItemManager",)


@dataclass(frozen=True)
class Item:
    id: int
    assistantType: str
    type: str
    attackKind: str
    attackExtra: str
    defenseKind: str
    defenseExtra: str
    attribute: str
    value: int
    subValue: int
    hitRate: int
    price: int
    weight: int

    __slots__ = tuple(__annotations__)

    @staticmethod
    def fromData(id: int, data: list[str]):
        return Item(
            id             = id,
            assistantType  = "",
            type           = data[0],
            attackKind     = data[1],
            attackExtra    = data[2],
            defenseKind    = data[3],
            defenseExtra   = data[4],
            attribute      = data[5],
            value          = int(data[6]) if data[6] else 0,
            subValue       = int(data[7]) if data[7] else 0,
            hitRate        = int(data[8]) if data[8] else 0,
            price          = int(data[9]) if data[9] else 0,
            weight         = int(data[10]) if data[10] else 0
        )

    @staticmethod
    def fromAssistantData(id: int, data: list[str]):
        return Item(
            id             = id,
            assistantType  = data[0],
            type           = "WEAPON",
            attackKind     = data[1],
            attackExtra    = data[2],
            defenseKind    = "",
            defenseExtra   = "",
            attribute      = data[3],
            value          = int(data[4]) if data[4] else 0,
            subValue       = 0,
            hitRate        = int(data[5]) if data[5] else 0,
            price          = 0,
            weight         = int(data[6]) if data[6] else 0
        )
    
    def isAtkHarm(self) -> bool:
        return self.attackExtra in ["COLD", "FEVER", "HELL", "HEAVEN", "FOG", "ILLUSION", "GLORY", "DARK_CLOUD"]

    def isDefHarm(self) -> bool:
        return self.defenseExtra in ["COLD", "FEVER", "HELL", "HEAVEN", "FOG", "ILLUSION", "GLORY", "DARK_CLOUD"]

    def getAtk(self) -> int:
        if self.attackKind == "ATK":
            return self.value
        if self.attackExtra in ["INCREASE_ATK", "ADD_ATTRIBUTE"]:
            if self.type in ["WEAPON", "MAGIC"]:
                return self.value
            elif self.type in ["PROTECTOR", "SUNDRY"]:
                return self.subValue
        return 0

    def getDef(self) -> int:
        if self.defenseKind == "DFS":
            if self.type == "WEAPON":
                return self.subValue
            elif self.type == "PROTECTOR":
                return self.value
        return 0

    def getAD(self) -> list[int]:
        return [self.getAtk(), self.getDef()]


class ItemManager:
    items: list[Item]
    itemsProbabilities: numpy.ndarray
    assistantItems: dict[str, list[Item]]
    assistantItemsProbabilities: dict[str, numpy.ndarray]
    randGen: numpy.random.Generator

    __slots__ = tuple(__annotations__)

    def __init__(self, dataFilename: str, assistantDataFilename: str):
        self.items = list()
        self.assistantItems = dict()
        self.randGen = numpy.random.default_rng()

        self.loadItems(dataFilename)
        self.loadAssistantItems(assistantDataFilename)

    def __contains__(self, id: int) -> bool:
        return any(item.id == id for item in self.items)
        
    def getItem(self, id: int) -> Item:
        for item in self.items:
            if item.id == id:
                return item
        assert False, "Tried to get innexistant item"

    def getRandomItem(self, types: list[str]) -> Item:
        item = None
        while item is None:
            chosen = self.items[random.randrange(len(self.items))]
            item = chosen if chosen.type in types else None
        return item

    def getProbRandomItems(self, count: int) -> list[Item]:
        if count == 0:
            return []
        return self.randGen.choice(self.items, count, p = self.itemsProbabilities) # type: ignore

    def getProbRandomAssistantItem(self, assistantType: str) -> Item:
        assert assistantType in self.assistantItems
        return self.randGen.choice(self.assistantItems[assistantType], 1, p = self.assistantItemsProbabilities[assistantType])[0] # type: ignore

    def loadItems(self, dataFilename: str):
        itemWeights = []
        with open(dataFilename, 'r') as f:
            for line in f:
                item = Item.fromData(len(self.items), line.rstrip("\n").split(","))
                self.items.append(item)
                itemWeights.append(item.weight)

        self.itemsProbabilities = numpy.array(list(map(float, itemWeights)))
        self.itemsProbabilities = self.itemsProbabilities / sum(itemWeights)

        print(f"ItemManager: Loaded {len(self.items)} items")

    def loadAssistantItems(self, dataFilename: str):
        itemWeights = {}
        with open(dataFilename, 'r') as f:
            for line in f:
                assistantItemData = line.rstrip("\n").split(",")
                assistantItemList = self.assistantItems.setdefault(assistantItemData[0], [])
                assistantItemWeights = itemWeights.setdefault(assistantItemData[0], [])

                item = Item.fromAssistantData(len(assistantItemList), assistantItemData)
                assistantItemList.append(item)
                assistantItemWeights.append(item.weight)

        self.assistantItemsProbabilities = {}
        for type, items in itemWeights.items():
            self.assistantItemsProbabilities[type] = numpy.array(list(map(float, items)))
            self.assistantItemsProbabilities[type] = self.assistantItemsProbabilities[type] / sum(items)

        print(f"ItemManager: Loaded {len(self.assistantItems)} assistant items")