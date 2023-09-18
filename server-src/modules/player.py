from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Iterator
if TYPE_CHECKING:
    from server import Server
    from modules.session import Session
    from modules.room import Room
from helpers.xmlbuilder import XMLBuilder, XMLNode
from modules.item import Item
from modules.bot import AIProcessor
from modules.assistant import Assistant
from modules.commandPiece import CommandPiece

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
    pieces: list[CommandPiece]
    assistant: Optional[Assistant]
    aiProcessor: Optional[AIProcessor]
    pendingUnillusion: bool
    pendingUnfog: bool

    __slots__ = tuple(__annotations__)

    def __init__(self, room: Room, sessionOrName: Session | str, team: str):
        if isinstance(sessionOrName, str):
            self.name = sessionOrName
            self.session = None
        else:
            self.name = sessionOrName.userName
            self.session = sessionOrName

        self.team = team

        self.server = room.server
        self.room = room

        self.aiProcessor = None

        self.reset()

    def __str__(self):
        return f"<Player {self.name}>"

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
        self.pieces = list()

        self.assistant = None

        self.pendingUnillusion = False
        self.pendingUnfog = False

    def enableAIProcessor(self):
        self.aiProcessor = AIProcessor(self)

    def disableAIProcessor(self):
        self.aiProcessor = None

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
        if self.assistant is not None:
            damage = self.assistant.absorbDamage(damage)
            if self.assistant.hp == 0:
                self.assistant = None
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
        assert harm in Item.ALL_DISEASES or harm in Item.ALL_HARMS

        if self.disease == "HEAVEN":
            self.takeDamage(999)
            self.worseChance = 0
            print(f"\"{self.name}\": FALL FROM THE HEAVEN!")
            return

        if harm in Item.ALL_DISEASES:
            if self.disease:
                idx = Item.ALL_DISEASES.index(self.disease)
                self.disease = harm if idx < Item.ALL_DISEASES.index(harm) else Item.ALL_DISEASES[idx + 1]
            else:
                self.disease = harm
            self.worseChance = 0
            print(f"\"{self.name}\" got disease: {self.disease}")
        elif harm not in self.harms:
            self.harms.append(harm)
            print(f"\"{self.name}\" got harm: {harm}")

    def unillusionPieces(self):
        builder = XMLBuilder("UNILLUSION")
        for piece in self.pieces:
            if piece.illusionItem is None:
                continue
            piece.writeXML(builder.item)
            piece.illusionItem = None
        if self.session is not None:
            self.session.sendXml(builder)
        self.pendingUnillusion = False

    def unfog(self):
        builder = XMLBuilder("UNFOG")
        for player in self.room.players:
            player.writeXML(builder.player)
        builder.inningAttacker(self.room.turn.attacker.name if self.room.turn.currentAttack is None else self.room.turn.currentAttack.attacker.name)
        if self.session is not None:
            self.session.sendXml(builder)
        self.pendingUnfog = False

    def removeAllHarms(self, onlyLower: bool = False):
        if not onlyLower:
            print(f"\"{self.name}\": Remove all harms")
            if "ILLUSION" in self.harms:
                self.pendingUnillusion = True
            if "FOG" in self.harms:
                self.pendingUnfog = True
            self.disease = ""
            self.worseChance = 0
            self.harms = []
            return

        print(f"\"{self.name}\": Remove lower harms")
        if self.disease in ["COLD", "FEVER"]:
            self.disease = ""
            self.worseChance = 0
        if "FOG" in self.harms:
            self.harms.remove("FOG")
            self.pendingUnfog = True
        if "GLORY" in self.harms:
            self.harms.remove("GLORY")

    def dealItem(self, id: int, isAction: bool = False) -> bool:
        assert id in self.server.itemManager

        if len(self.pieces) == 16:
            print(f"{self.name} deal failed because hand is full")
            return False

        print(f"{self.name} deal {id}")
        piece = CommandPiece(self.server.itemManager.getItem(id))

        if "ILLUSION" in self.harms and piece.item.canBeAffectedByIllusion() and not isAction:
            illusionId = id
            if random.randrange(0, 2) == 1:
                illusionId = self.server.itemManager.getIllusionForItem(id)
            piece.illusionItem = self.server.itemManager.getItem(illusionId)
            if illusionId != id:
                print(f"{self.name} previous deal was afflicted by illusion and became {illusionId}")

        self.pieces.append(piece)

        if not isAction and self.session is not None:
            builder = XMLBuilder("DEAL")
            builder.item(str(piece.getItemOrIllusion().id))
            self.session.sendXml(builder)

        return True

    def hasOwnedPiece(self, ownedPiece: CommandPiece) -> bool:
        return ownedPiece in self.pieces

    def hasMagic(self, id: int) -> bool:
        return id in self.magics

    def getItems(self, bypassIllusion: bool = True) -> Iterator[Item]:
        for piece in self.pieces:
            yield piece.item if bypassIllusion or piece.illusionItem is None else piece.illusionItem

    def getRandomPiece(self) -> Optional[CommandPiece]:
        if len(self.pieces) == 0:
            return None
        return random.choice(self.pieces)

    def getRandomMagic(self) -> int:
        if len(self.magics) == 0:
            return 0
        return random.choice(self.magics)

    def discardPiece(self, ownedPiece: CommandPiece) -> bool:
        if not self.hasOwnedPiece(ownedPiece):
            print(self.pieces)
            assert False, f"\"{self.name}\" tried to discard piece ({ownedPiece}) that he doesn't have"

        print(f"{self.name} discard piece {ownedPiece}")
        self.pieces.remove(ownedPiece)
        return True

    def discardMagic(self, id: int) -> bool:
        if not self.hasMagic(id):
            assert False, f"\"{self.name}\" tried to discard magic (id {id}) that he doesn't have"

        print(f"{self.name} discard magic {id}")
        self.magics.remove(id)
        return True

    def getOwnedPieceById(self, id: int) -> Optional[CommandPiece]:
        return next((piece for piece in self.pieces if piece.item.id == id), None)

    def getOwnedPiece(self, otherPiece: CommandPiece, exceptPieces: list[CommandPiece] = []) -> Optional[CommandPiece]:
        if otherPiece.illusionItemIndex != -1:
            illusionIndex = 0
            for piece in self.pieces:
                if piece.illusionItem is not None and piece.illusionItem.id == otherPiece.item.id:
                    if illusionIndex == otherPiece.illusionItemIndex and piece not in exceptPieces:
                        return piece
                    illusionIndex += 1
            return None
        else:
            return next((piece for piece in self.pieces if piece.item.id == otherPiece.item.id and piece.illusionItem is None and piece not in exceptPieces), None)

    def usePiece(self, ownedPiece: CommandPiece, noMPCost: bool):
        if not self.hasOwnedPiece(ownedPiece):
            print(self.pieces)
            assert False, f"\"{self.name}\" tried to use an piece ({ownedPiece}) that he doesn't have"

        item = ownedPiece.item
        if item.type == "FIXED":
            # FIXED artifacts are eternal.
            pass
        elif item.type == "MAGIC":
            assert noMPCost or self.mp >= item.subValue, f"\"{self.name}\" tried to use magic (id {id}) with not enough MP ({self.mp} < {item.subValue})"
            self.magics.append(ownedPiece.item.id)
            self.pieces.remove(ownedPiece)
            if not noMPCost:
                self.mp -= item.subValue
        else:
            self.pieces.remove(ownedPiece)

    def useMagic(self, id: int, noMPCost: bool):
        if not self.hasMagic(id):
            print(self.magics)
            assert False, f"\"{self.name}\" tried to use an magic ({id}) that he doesn't have"

        item = self.server.itemManager.getItem(id)
        assert noMPCost or self.mp >= item.subValue, f"\"{self.name}\" tried to use magic (id {id}) with not enough MP ({self.mp} < {item.subValue})"

        if not noMPCost:
            self.mp -= item.subValue

    def writeXML(self, bPlayer: XMLNode):
        bPlayer.name(self.name)
        bPlayer.team(self.team)
        if self.ready:
            bPlayer.isReady  # <isReady />
        if self.dead:
            bPlayer.isDead  # <isDead />
        if self.lost:
            bPlayer.isLost
        if self.finished:
            bPlayer.isFinished
        if self.waitingAttackTurn:
            bPlayer.isWaitingAttackTurn
        bPlayer.power(key="HP")(str(self.hp))
        bPlayer.power(key="MP")(str(self.mp))
        bPlayer.power(key="YEN")(str(self.yen))
        if self.disease:
            bPlayer.disease(self.disease)
        for harm in self.harms:
            bPlayer.harm(harm)
        if self.assistant is not None:
            bAssistant = bPlayer.assistant
            bAssistant.type(self.assistant.type)
            bAssistant.hp(str(self.assistant.hp))
