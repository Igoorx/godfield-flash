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
        
    def canBeDefendedBy(self, defenseAttr: Optional[str]):
        if not self.attribute or self.attribute == "DARK":
            return True
        if not defenseAttr:
            return self.attribute == "DARK"
        if self.attribute == "FIRE":
            return defenseAttr in ["WATER", "LIGHT"]
        elif self.attribute == "WATER":
            return defenseAttr in ["FIRE", "LIGHT"]
        elif self.attribute == "TREE":
            return defenseAttr in ["SOIL", "LIGHT"]
        elif self.attribute == "SOIL":
            return defenseAttr in ["TREE", "LIGHT"]
        elif self.attribute == "LIGHT":
            return defenseAttr == "DARK"
        assert False, "Unknown attribute!"

    def isValidAttackItem(self, item: Item, isFirstPiece: bool, hasUsedMagic: bool) -> bool:
        if isFirstPiece:
            return item.type != "PROTECTOR" and (item.type not in ["MAGIC", "SUNDRY"] or item.attackKind != "")
        
        return item.attackKind not in ["DO_NOTHING", "DISCARD", "SELL", "EXCHANGE", "MYSTERY"] and\
                ((item.attackExtra in ["INCREASE_ATK", "DOUBLE_ATK", "WIDE_ATK", "ADD_ATTRIBUTE"] and\
                    self.pieceList[0].item.type == "WEAPON" and self.pieceList[0].item.hitRate == 0) or\
                    (hasUsedMagic and item.attackExtra == "MAGIC_FREE"))