from __future__ import annotations
from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from helpers.xmlbuilder import XMLNode
    from modules.item import Item, ItemManager

__all__ = ("CommandPiece",)


class CommandPiece:
    item: Item
    illusionItem: Optional[Item]
    illusionItemIndex: int
    isAbility: bool
    abilityIndex: int
    costMP: int

    __slots__ = tuple(__annotations__)

    def __init__(self, item: Item, isAbility: bool = False):
        self.item = item
        self.illusionItem = None
        self.illusionItemIndex = -1
        self.isAbility = isAbility

        self.abilityIndex = -1
        self.costMP = 0

    def __str__(self):
        return f"<CommandPiece Item={self.item}, IllusionItem={self.illusionItem if self.illusionItem else '[Not a Illusion]'}>"
    
    def __repr__(self):
        return f"<CommandPiece Item={self.item}{f', IllusionItem={self.illusionItem}' if self.illusionItem else ''}{f', IllusionItemIndex={self.illusionItemIndex}' if self.illusionItemIndex != -1 else ''}>"
    
    def clone(self) -> CommandPiece:
        piece = CommandPiece(self.item)
        piece.illusionItem = self.illusionItem
        piece.illusionItemIndex = self.illusionItemIndex
        piece.isAbility = self.isAbility

        piece.abilityIndex = self.abilityIndex
        piece.costMP = self.costMP
        return piece
    
    @staticmethod
    def fromDict(itemManager: ItemManager, x: dict):
        piece = CommandPiece(itemManager.getItem(int(x["item"])))
        piece.illusionItemIndex = int(x["illusionItemIndex"]) if "illusionItemIndex" in x else -1
        piece.abilityIndex = int(x["abilityIndex"]) if "abilityIndex" in x else -1
        piece.isAbility = "isAbility" in x
        return piece
    
    def writeXML(self, piece: XMLNode):
        piece.item(str(self.item.id))
        if self.item.assistantType:
            piece.assistantType(self.item.assistantType)
        if self.illusionItem is not None:
            piece.illusionItem(str(self.illusionItem.id))
        if self.abilityIndex != -1:
            piece.abilityIndex(str(self.abilityIndex))
        if self.costMP != 0:
            piece.costMP(str(self.costMP))

    def getItemOrIllusion(self) -> Item:
        return self.item if self.illusionItem is None else self.illusionItem
