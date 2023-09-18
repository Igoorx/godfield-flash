from typing import Optional
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

    ALL_DISEASES = ["COLD", "FEVER", "HELL", "HEAVEN"]
    ALL_HARMS = ["FOG", "ILLUSION", "GLORY", "DARK_CLOUD"]
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
        return self.attackExtra in Item.ALL_DISEASES + Item.ALL_HARMS

    def isDefHarm(self) -> bool:
        return self.defenseExtra in Item.ALL_DISEASES + Item.ALL_HARMS

    def hasSpecialWeaponDefense(self):
        return self.defenseExtra in ["REFLECT_WEAPON", "FLICK_WEAPON", "BLOCK_WEAPON"]

    def hasSpecialMagicDefense(self):
        return self.defenseExtra in ["REFLECT_MAGIC", "FLICK_MAGIC", "BLOCK_MAGIC"]

    def canBeAffectedByIllusion(self) -> bool:
        if self.type in ["TRADE", "MAGIC"]:
            return False
        return True

    def isSimilarTo(self, other: 'Item') -> bool:
        if self.type in ["TRADE", "MAGIC"]:
            return False

        if self.defenseKind != other.defenseKind:
            return False

        if self.hitRate != 0 and other.hitRate == 0:
            return False

        # Check specific conditions for attackExtra
        if self.attackExtra in ["MAGIC_FREE", "PESTLE"] and \
            other.attackExtra != self.attackExtra:
            return False
        if self.attackExtra in ["INCREASE_ATK", "ADD_ATTRIBUTE"] and \
            other.attackExtra not in ["INCREASE_ATK", "ADD_ATTRIBUTE"]:
            return False
        if self.attackExtra in ["REVIVE", "MORTAR"] and \
            other.attackExtra not in ["REVIVE", "MORTAR"]:
            return False

        # Check specific conditions for defenseKind
        if self.attribute != "" and self.defenseKind in ["DFS", "COUNTER"] and other.attribute != self.attribute:
            return False

        # Check specific conditions for defenseExtra
        if self.defenseExtra in ["REMOVE_ATTRIBUTE", "REFLECT_ANY"] and \
            other.defenseExtra != self.defenseExtra:
            return False
        if self.hasSpecialWeaponDefense() and not other.hasSpecialWeaponDefense():
             return False
        if self.hasSpecialMagicDefense() and not other.hasSpecialMagicDefense():
             return False

        return True

    def isReplaceableBy(self, other: 'Item') -> bool:
        return self.isSimilarTo(other) and other.isSimilarTo(self)

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

    @staticmethod
    def checkDefense(attackAttr: Optional[str], defenseAttr: Optional[str]):
        if not attackAttr or attackAttr == "DARK":
            return True

        if not defenseAttr:
            return attackAttr == "DARK"

        defenseMapping = {
            "FIRE": ["WATER", "LIGHT"],
            "WATER": ["FIRE", "LIGHT"],
            "TREE": ["SOIL", "LIGHT"],
            "SOIL": ["TREE", "LIGHT"],
            "LIGHT": ["DARK"]
        }

        assert attackAttr in defenseMapping, f"Unknown attribute \"{attackAttr}\"!"
        return defenseAttr in defenseMapping[attackAttr]


class ItemManager:
    items: list[Item]
    itemsByType: dict[str, list[Item]]
    itemsProbabilities: numpy.ndarray
    assistantItems: dict[str, list[Item]]
    assistantItemsProbabilities: dict[str, numpy.ndarray]
    randGen: numpy.random.Generator

    __slots__ = tuple(__annotations__)

    def __init__(self, dataFilename: str, assistantDataFilename: str):
        self.items = list()
        self.itemsByType = dict()
        self.assistantItems = dict()
        self.randGen = numpy.random.default_rng()

        self.loadItems(dataFilename)
        self.loadAssistantItems(assistantDataFilename)

    def __contains__(self, id: int) -> bool:
        return any(item.id == id for item in self.items)

    def getItem(self, id: int) -> Item:
        item = next((item for item in self.items if item.id == id), None)
        assert item is not None, f"Tried to get inexistent item {id}!"
        return item

    def getIllusionForItem(self, id: int) -> int:
        item = self.getItem(id)
        itemsOfSameType = list(self.itemsByType[item.type])
        random.shuffle(itemsOfSameType)
        for chosen in itemsOfSameType:
            if item.id == chosen.id or chosen.weight == 0:
                continue
            if item.isReplaceableBy(chosen):
                return chosen.id
        return id

    def getProbRandomItems(self, count: int) -> list[Item]:
        if count == 0:
            return []
        return self.randGen.choice(self.items, count, p = self.itemsProbabilities) # type: ignore

    def getProbRandomItem(self) -> Item:
        return self.randGen.choice(self.items, 1, p = self.itemsProbabilities)[0] # type: ignore

    def getProbRandomAssistantItem(self, assistantType: str) -> Item:
        assert assistantType in self.assistantItems
        return self.randGen.choice(self.assistantItems[assistantType], 1, p = self.assistantItemsProbabilities[assistantType])[0] # type: ignore

    def loadItems(self, dataFilename: str):
        itemWeights = []
        with open(dataFilename, 'r') as f:
            for line in f:
                item = Item.fromData(len(self.items), line.rstrip("\n").split(","))
                self.items.append(item)
                self.itemsByType.setdefault(item.type, []).append(item)
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