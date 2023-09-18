from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from server import Server
    from modules.room import Room
    from modules.item import Item
    from modules.player import Player
from modules.attackData import AttackData
from modules.commandPiece import CommandPiece

import random

__all__ = ("Assistant",)


class Assistant:
    type: str
    hp: int
    summoner: Player
    room: Room
    server: Server

    VALID_TYPES = ["MARS", "MERCURY", "JUPITER", "SATURN", "URANUS", "PLUTO", "NEPTUNE", "VENUS", "EARTH", "MOON"]
    __slots__ = tuple(__annotations__)

    def __init__(self, summoner: Player, type: str):
        self.summoner = summoner
        self.room = summoner.room
        self.server = summoner.server
        self.type = type
        self.hp = 20

    def __str__(self):
        return f"<Assistant {self.type}>"

    @staticmethod
    def createRandom(summoner: Player):
        return Assistant(summoner, random.choice(Assistant.VALID_TYPES))

    def absorbDamage(self, damage: int) -> int:
        self.hp -= damage
        damage = 0
        if self.hp < 0:
            damage = self.hp * -1
            self.hp = 0
        return damage

    def onAttackOpportunity(self):
        print(f"{self.summoner.name}'s {self.type} assistant attack!")

        if self.type == "EARTH":
            itemList = self.buildEarthAttack()
        elif self.type == "MOON":
            itemList = self.buildMoonAttack()
        else:
            itemList = [self.server.itemManager.getProbRandomAssistantItem(self.type)]

        target = self.decideAttackTarget(itemList)
        newAttack = AttackData(self.summoner, target, [CommandPiece(item) for item in itemList])
        newAttack.assistantType = self.type
        self.room.turn.queueAttack(newAttack, True)

    def buildEarthAttack(self) -> list[Item]:
        secondItem = self.server.itemManager.getProbRandomItem()
        if secondItem.type != "MAGIC":
            if secondItem.attackKind == "SELL":
                return [secondItem, self.server.itemManager.getProbRandomItem()]
            elif secondItem.attackKind in ["ATK", "BUY"]:
                return [secondItem]
        itemList = [self.server.itemManager.getProbRandomAssistantItem(self.type)] # ADD_ITEM
        itemList.append(secondItem)
        return itemList

    def buildMoonAttack(self) -> list[Item]:
        secondItem = None
        while secondItem is None or secondItem.type != "MAGIC" or secondItem.defenseExtra in ["FLICK_MAGIC", "BLOCK_WEAPON"]:
            secondItem = self.server.itemManager.getProbRandomItem()
        if secondItem.attackExtra not in ["WIDE_ATK", "DOUBLE_ATK"]:
            return [secondItem]
        itemList = [self.server.itemManager.getProbRandomAssistantItem(self.type)] # ATK
        itemList.append(secondItem)
        return itemList

    def decideAttackTarget(self, itemList: list[Item]) -> Player:
        if (itemList[0].attackKind == "ATK" and itemList[0].hitRate == 0) or \
            itemList[0].attackKind in ["SELL", "BUY", "ABSORB_YEN", "ADD_HARM", "REMOVE_ITEMS", "REMOVE_ABILITIES"]:
            return self.room.getRandomAliveEnemy(self.summoner)
        elif (itemList[0].attackKind == "INCREASE_MP" and not itemList[0].isAtkHarm()) or \
              itemList[0].attackKind in ["INCREASE_HP", "INCREASE_YEN", "REMOVE_LOWER_HARMS", "REMOVE_ALL_HARMS", "ADD_ITEM", "SET_ASSISTANT"]:
            return self.room.getRandomAliveAlly(self.summoner, False)
        return self.summoner
