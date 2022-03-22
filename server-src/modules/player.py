from __future__ import annotations
from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from server import Server
    from modules.session import Session
    from modules.room import Room
from helpers.xmlbuilder import XMLBuilder
from modules.bot import AIProcessor

import random

__all__ = ("Player",)


class Player:
    name: str
    team: str
    session: Optional[Session]
    server: Server
    room: Room
    ready: bool
    dead: bool
    lost: bool
    finished: bool
    waitingAttackTurn: bool
    hp: int
    mp: int
    yen: int
    disease: str
    worseChance: int
    harms: list[str]
    deal: int
    magics: list[int]
    items: list[int]
    assistantType: str
    assistantHP: int
    aiProcessor: Optional[AIProcessor]

    __slots__ = tuple(__annotations__)

    def __init__(self, session: Optional[Session], name: str, team: str):
        self.name = name
        self.team = team

        self.session = session
        if session is not None:
            assert session.room is not None
            self.server = session.server
            self.room = session.room

        self.aiProcessor = None

        self.reset()

    def __str__(self):
        return f"<Player {self.name}>"

    def enableAIProcessor(self):
        self.aiProcessor = AIProcessor(self)

    def disableAIProcessor(self):
        self.aiProcessor = None

    def reset(self):
        self.ready = False
        self.dead = False
        self.lost = False
        self.finished = False
        self.waitingAttackTurn = False

        self.hp = 40
        self.mp = 10
        self.yen = 20

        self.disease = str()
        self.worseChance = int()
        self.harms = list()

        self.deal = 10

        self.magics = list()
        self.items = list()

        self.assistantType = str()
        self.assistantHP = 0

    def isEnemy(self, other: Player):
        return other != self and (other.team == "SINGLE" or other.team != self.team)

    def increaseHP(self, amount: int):
        assert amount >= 0
        self.hp = min(99, self.hp + amount)

    def increaseMP(self, amount: int):
        assert amount >= 0
        self.mp = min(99, self.mp + amount)

    def increaseYen(self, amount: int):
        assert amount >= 0
        self.yen = min(99, self.yen + amount)

    def takeDamage(self, damage: int):
        assert damage >= 0
        if self.assistantHP > 0:
            self.assistantHP -= damage
            damage = 0
            if self.assistantHP < 0:
                damage = self.assistantHP * -1
                self.assistantHP = 0
            if self.assistantHP == 0:
                self.assistantType = ""
        self.hp = max(0, self.hp - damage)

    def decreaseYen(self, amount):
        self.yen -= amount
        if self.yen >= 0:
            return
        self.mp -= self.yen * -1
        self.yen = 0
        if self.mp >= 0:
            return
        self.hp = max(0, self.hp - self.mp * -1)
        self.mp = 0

    def hasLowerDisease(self) -> bool:
        return self.disease in ["COLD", "FEVER"] or any(harm in ["FOG", "GLORY"] for harm in self.harms)

    def diseaseEffect(self) -> bool:
        assert self.disease and self.hp != 0, f"\"{self.name}\": Invalid call to diseaseEffect (Disease: {self.disease}, HP: {self.hp})"
        
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
            assert False, f"Unimplemented disease: {self.disease}"
        
        if damage >= 0:
            self.takeDamage(damage)
        else:
            self.increaseHP(-damage)
        return True

    def addHarm(self, harm: str):
        diseases = ["COLD", "FEVER", "HELL", "HEAVEN"]
        if harm in diseases:
            if self.disease:
                if self.disease == "HEAVEN":
                    print("FALL FROM THE HEAVEN")
                    self.hp = 0
                    self.assistantType = ""
                    self.assistantHP = 0
                else:
                    idx = diseases.index(self.disease)
                    self.disease = harm if idx < diseases.index(harm) else diseases[idx + 1]
            else:
                self.disease = harm
            self.worseChance = 0
        elif harm not in self.harms:
            self.harms.append(harm)
        print(f"\"{self.name}\": Current Harm: {self.harms}, Current Disease: {self.disease}")

    def removeAllHarms(self, onlyLower: bool = False):
        if not onlyLower:
            print("Remove all harms")
            self.disease = ""
            self.worseChance = 0
            self.harms = []
            return

        print(f"\"{self.name}\": Remove lower harms")
        if self.disease in ["COLD", "FEVER"]:
            self.disease = ""
            self.worseChance = 0
        if "FOG" in self.harms:
            # TODO: Properly implement "UNFOG"
            self.harms.remove("FOG")
        if "GLORY" in self.harms:
            self.harms.remove("GLORY")

    def dealItem(self, id: int, noXml: bool = False) -> bool:
        assert id in self.server.itemManager

        if len(self.items) == 16:
            print(f"{self.name} deal failed because hand is full")
            return False
        
        print(f"{self.name} deal {id}")
        self.items.append(id)

        if not noXml and self.session is not None:
            builder = XMLBuilder("DEAL")
            builder.item(str(id))
            self.session.sendXml(builder)
        
        return True

    def hasItem(self, id: int) -> bool:
        return id in self.items

    def hasAttackKind(self, kind: str) -> bool:
        for id in self.items:
            item = self.server.itemManager.getItem(id)
            if item.attackKind == kind:
                return True
        return False

    def hasMagic(self, id: int) -> bool:
        return id in self.magics

    def getRandomItem(self) -> int:
        if len(self.items) == 0:
            return 0
        return random.choice(self.items)

    def getRandomMagic(self) -> int:
        if len(self.magics) == 0:
            return 0
        return random.choice(self.magics)

    def discardItem(self, id: int) -> bool:
        if not self.hasItem(id):
            assert False, f"\"{self.name}\" tried to discard item (id {id}) that he doesn't have"
        
        print(f"{self.name} discard item {id}")
        self.items.remove(id)
        return True

    def discardMagic(self, id: int) -> bool:
        if not self.hasMagic(id):
            assert False, f"\"{self.name}\" tried to discard magic (id {id}) that he doesn't have"
        
        print(f"{self.name} discard magic {id}")
        self.magics.remove(id)
        return True

    def useItem(self, id: int, noMPCost: bool):
        if not self.hasItem(id):
            print(self.items)
            assert False, f"\"{self.name}\" tried to use an item (id {id}) that he doesn't have"
        
        item = self.server.itemManager.getItem(id)
        if item.type == "FIXED":
            # FIXED artifacts are eternal.
            pass
        elif item.type == "MAGIC":
            assert noMPCost or self.mp >= item.subValue, f"\"{self.name}\" tried to use magic (id {id}) with not enough MP ({self.mp} < {item.subValue})"
            self.magics.append(id)
            self.items.remove(id)
            if not noMPCost:
                self.mp -= item.subValue
        else:
            self.items.remove(id)

    def tryUseMagic(self, id: int, noMPCost: bool) -> bool:
        if not self.hasMagic(id):
            return False
        
        item = self.server.itemManager.getItem(id)
        assert noMPCost or self.mp >= item.subValue, f"\"{self.name}\" tried to use magic (id {id}) with not enough MP ({self.mp} < {item.subValue})"
        
        if not noMPCost:
            self.mp -= item.subValue
        return True
