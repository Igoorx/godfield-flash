from __future__ import annotations
from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from modules.item import Item
    from modules.player import Player

__all__ = ("AttackData",)


class AttackData:
    attacker: Player
    defender: Player
    isAction: bool
    isLast: bool
    isCounter: bool
    isRetargeted: bool
    damage: int
    chance: int
    extra: list[str]
    attribute: Optional[str]
    piece: list[Item]
    abilityIndex: Optional[int]
    mortarId: Optional[int]
    assistantType: Optional[str]
    decidedValue: Optional[int]
    decidedHP: Optional[int]
    decidedMystery: Optional[str]
    decidedExchange: Optional[dict[str, int]]
    decidedItem: Optional[Item]
    decidedAssistant: Optional[str]

    __slots__ = tuple(__annotations__)

    def __init__(self, attacker: Player, defender: Player, piece: list[Item]):
        self.attacker = attacker
        self.defender = defender

        self.isAction = False
        self.isLast = False
        self.isCounter = False
        self.isRetargeted = False
        
        self.damage = -1
        self.chance = 0
        self.extra = list()
        self.attribute = None
        self.piece = piece

        self.abilityIndex = None
        self.mortarId = None
        self.assistantType = None

        self.decidedValue = None
        self.decidedHP = None
        self.decidedMystery = None
        self.decidedExchange = None
        self.decidedItem = None
        self.decidedAssistant = None

    def __str__(self):
        return f"Attacker: {self.attacker}, Defender: {self.defender}, Damage: {self.damage}, Extra: {self.extra}, Attribute: {self.attribute}"

    def clone(self) -> AttackData:
        clone = AttackData(self.attacker, self.defender, self.piece)

        clone.isAction = self.isAction
        clone.isLast = self.isLast
        clone.isCounter = self.isCounter
        clone.isRetargeted = self.isRetargeted
        
        clone.damage = self.damage
        clone.chance = self.chance
        clone.extra = self.extra
        clone.attribute = self.attribute

        clone.abilityIndex = self.abilityIndex
        clone.mortarId = self.mortarId
        clone.assistantType = self.assistantType

        clone.decidedValue = self.decidedValue
        clone.decidedHP = self.decidedHP
        clone.decidedMystery = self.decidedMystery
        clone.decidedExchange = self.decidedExchange
        clone.decidedItem = self.decidedItem
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