from __future__ import annotations
from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from modules.item import Item
    from modules.commandPiece import CommandPiece
    from modules.player import Player

__all__ = ("AttackData",)


class AttackData:
    attacker: Player
    defender: Player
    isAction: bool
    isLast: bool
    isCounter: bool
    damage: int
    chance: int
    extra: list[str]
    attribute: Optional[str]
    pieceList: list[CommandPiece]
    mortar: Optional[CommandPiece]
    assistantType: Optional[str]
    decidedValue: Optional[int]
    decidedHP: Optional[int]
    decidedMystery: Optional[str]
    decidedExchange: Optional[dict[str, int]]
    decidedPiece: Optional[CommandPiece]
    decidedAssistant: Optional[str]

    __slots__ = tuple(__annotations__)

    def __init__(self, attacker: Player, defender: Player, piece: list[CommandPiece]):
        self.attacker = attacker
        self.defender = defender

        self.isAction = False
        self.isLast = False
        self.isCounter = False

        self.damage = -1
        self.chance = 0
        self.extra = list()
        self.attribute = None
        self.pieceList = piece

        self.mortar = None
        self.assistantType = None

        self.decidedValue = None
        self.decidedHP = None
        self.decidedMystery = None
        self.decidedExchange = None
        self.decidedPiece = None
        self.decidedAssistant = None

    def __str__(self):
        return f"<AttackData Attacker={self.attacker}{' (assistant)' if self.assistantType else ''}, Defender={self.defender}, Damage={self.damage}, Extra={self.extra}, Attribute={self.attribute}, DecidedValue={self.decidedValue}>"

    def __repr__(self):
        return f"<AttackData Attacker={self.attacker}{' (assistant)' if self.assistantType else ''}, Defender={self.defender}, Damage={self.damage}, Extra={self.extra}, Attribute={self.attribute}, DecidedValue={self.decidedValue}>"

    def clone(self) -> AttackData:
        clone = AttackData(self.attacker, self.defender, self.pieceList)

        clone.isAction = self.isAction
        clone.isLast = self.isLast
        clone.isCounter = self.isCounter

        clone.damage = self.damage
        clone.chance = self.chance
        clone.extra = self.extra
        clone.attribute = self.attribute

        clone.mortar = self.mortar
        clone.assistantType = self.assistantType

        clone.decidedValue = self.decidedValue
        clone.decidedHP = self.decidedHP
        clone.decidedMystery = self.decidedMystery
        clone.decidedExchange = self.decidedExchange
        clone.decidedPiece = self.decidedPiece
        clone.decidedAssistant = self.decidedAssistant
        return clone

    def isValidAttackItem(self, item: Item, isFirstPiece: bool, hasUsedMagic: bool) -> bool:
        if isFirstPiece:
            if item.type == "PROTECTOR":
                return False
            return item.type not in ["MAGIC", "SUNDRY"] or item.attackKind != ""

        if item.attackKind in ["DO_NOTHING", "DISCARD", "SELL", "EXCHANGE", "MYSTERY"]:
            return False

        if hasUsedMagic and item.attackExtra == "MAGIC_FREE":
            return True

        firstPiece = self.pieceList[0]
        return (
            firstPiece.item.type == "WEAPON"
            and firstPiece.item.hitRate == 0
            and item.attackExtra in ["INCREASE_ATK", "DOUBLE_ATK", "WIDE_ATK", "ADD_ATTRIBUTE"]
        )