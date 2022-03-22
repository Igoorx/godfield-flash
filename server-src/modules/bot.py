from __future__ import annotations
from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from server import Server
    from modules.room import Room
    from modules.player import Player
    from modules.item import Item
from dataclasses import dataclass
from modules.attack import AttackData

from typing import Optional
import random

__all__ = ("AIProcessor",)


@dataclass
class EnemyStats:
    lastHP: Optional[int] = None
    damageCombo: int = 0

class AIProcessor:
    player: Player
    room: Room
    server: Server
    enemyStats: dict[str, EnemyStats]
    possiblyDefenceless: list[Player]

    __slots__ = tuple(__annotations__)

    def __init__(self, player: Player):
        self.player = player
        self.room = player.room
        self.server = player.server
        self.enemyStats = dict()
        self.possiblyDefenceless = list()

    def checkEnemyStats(self):
        for player in self.room.players:
            if not player.isEnemy(self.player):
                continue

            if player.dead:
                if player in self.possiblyDefenceless:
                    self.possiblyDefenceless.remove(player)
                if player.name in self.enemyStats:
                    del self.enemyStats[player.name]
                continue

            stats = None
            if player.name not in self.enemyStats:
                stats = EnemyStats()
                self.enemyStats[player.name] = stats
            else:
                stats = self.enemyStats[player.name]

            if stats.lastHP is not None:
                if stats.lastHP > player.hp:
                    # Took damage
                    stats.damageCombo += 1

                    if stats.damageCombo > 1 and not player in self.possiblyDefenceless:
                        # Possibly defenseless
                        self.possiblyDefenceless.append(player)
                elif stats.lastHP <= player.hp:
                    # Didn't took damage
                    stats.damageCombo = 0

            stats.lastHP = player.hp

        print(f"Enemy Stats: {self.enemyStats}")

    def getItemByAK(self, kind: str) -> Optional[Item]:
        for id in self.player.items:
            item = self.server.itemManager.getItem(id)

            if item.type == "MAGIC" and self.player.mp < item.subValue:
                continue
            if item.attackKind == kind:
                return item
        return None

    def getItemsByAE(self, extra: str, attr: Optional[str] = None) -> list[Item]:
        items = []
        for id in self.player.items:
            item = self.server.itemManager.getItem(id)

            if item.type == "MAGIC" and self.player.mp < item.subValue:
                continue
            if attr is not None and item.attribute != attr:
                continue
            if item.attackExtra == extra:
                items.append(item)
        for id in self.player.magics:
            item = self.server.itemManager.getItem(id)
            
            if self.player.mp < item.subValue:
                continue
            if attr is not None and item.attribute != attr:
                continue
            if item.attackExtra == extra:
                items.append(item)
        return items

    def getItemsDamage(self, items: list[Item]) -> int:
        damage = 0
        for item in items:
            if item.attackExtra == "DOUBLE_ATK":
                damage *= 2
            else:
                damage += item.getAtk()
        return damage

    def getDefenseItems(self, forAttribute: str) -> list[Item]:
        items = []
        for id in self.player.items:
            item = self.server.itemManager.getItem(id)

            if item.defenseKind == "DFS":
                if item.type == "MAGIC" and self.player.mp < item.subValue:
                    continue
                if forAttribute == "FIRE" and item.attribute not in ["WATER", "LIGHT"]:
                    continue
                elif forAttribute == "WATER" and item.attribute not in ["FIRE", "LIGHT"]:
                    continue
                elif forAttribute == "TREE" and item.attribute not in ["SOIL", "LIGHT"]:
                    continue
                elif forAttribute == "SOIL" and item.attribute not in ["TREE", "LIGHT"]:
                    continue
                elif forAttribute == "LIGHT" and item.attribute not in ["DARK"]:
                    continue
                items.append(item)
        for id in self.player.magics:
            item = self.server.itemManager.getItem(id)

            if self.player.mp < item.subValue:
                continue
            
            if item.defenseKind == "DFS":
                if forAttribute == "FIRE" and item.attribute not in ["WATER", "LIGHT"]:
                    continue
                elif forAttribute == "WATER" and item.attribute not in ["FIRE", "LIGHT"]:
                    continue
                elif forAttribute == "TREE" and item.attribute not in ["SOIL", "LIGHT"]:
                    continue
                elif forAttribute == "SOIL" and item.attribute not in ["TREE", "LIGHT"]:
                    continue
                elif forAttribute == "LIGHT" and item.attribute not in ["DARK"]:
                    continue
                items.append(item)
        return items

    def getCounterRings(self, forAttribute: str) -> list[Item]:
        items = []
        for id in self.player.items:
            item = self.server.itemManager.getItem(id)

            if item.defenseKind == "COUNTER":
                if forAttribute == "FIRE" and item.attribute not in ["WATER", "LIGHT"]:
                    continue
                elif forAttribute == "WATER" and item.attribute not in ["FIRE", "LIGHT"]:
                    continue
                elif forAttribute == "TREE" and item.attribute not in ["SOIL", "LIGHT"]:
                    continue
                elif forAttribute == "SOIL" and item.attribute not in ["TREE", "LIGHT"]:
                    continue
                elif forAttribute == "LIGHT" and item.attribute not in ["DARK"]:
                    continue
                items.append(item)
        return items

    def getCounterItem(self, forAttribute: Optional[str], counter: bool, magic: bool, weapon: bool) -> Optional[Item]:
        for id in self.player.items:
            item = self.server.itemManager.getItem(id)

            if "REFLECT" in item.defenseExtra or\
               "FLICK" in item.defenseExtra or\
               "BLOCK" in item.defenseExtra:
                if ("MAGIC" in item.defenseExtra and not magic) or\
                   ("WEAPON" in item.defenseExtra and not weapon):
                    continue
                if item.type == "MAGIC" and self.player.mp < item.subValue:
                    continue
                if item.defenseExtra == "REFLECT_ANY":
                    return item
                elif forAttribute is None or counter:
                    continue
                elif forAttribute == "FIRE" and item.attribute not in ["WATER", "LIGHT"]:
                    continue
                elif forAttribute == "WATER" and item.attribute not in ["FIRE", "LIGHT"]:
                    continue
                elif forAttribute == "TREE" and item.attribute not in ["SOIL", "LIGHT"]:
                    continue
                elif forAttribute == "SOIL" and item.attribute not in ["TREE", "LIGHT"]:
                    continue
                elif forAttribute == "LIGHT" and item.attribute not in ["DARK"]:
                    continue
                elif forAttribute == "DARK" and item.attribute not in ["LIGHT"]:
                    continue
                return item
        for id in self.player.magics:
            item = self.server.itemManager.getItem(id)

            if self.player.mp < item.subValue:
                continue

            if "REFLECT" in item.defenseExtra or\
               "FLICK" in item.defenseExtra or\
               "BLOCK" in item.defenseExtra:
                if ("MAGIC" in item.defenseExtra and not magic) or\
                   ("WEAPON" in item.defenseExtra and not weapon):
                    continue
                if item.defenseExtra == "REFLECT_ANY":
                    return item
                elif forAttribute is None or counter:
                    continue
                elif forAttribute == "FIRE" and item.attribute not in ["WATER", "LIGHT"]:
                    continue
                elif forAttribute == "WATER" and item.attribute not in ["FIRE", "LIGHT"]:
                    continue
                elif forAttribute == "TREE" and item.attribute not in ["SOIL", "LIGHT"]:
                    continue
                elif forAttribute == "SOIL" and item.attribute not in ["TREE", "LIGHT"]:
                    continue
                elif forAttribute == "LIGHT" and item.attribute not in ["DARK"]:
                    continue
                elif forAttribute == "DARK" and item.attribute not in ["LIGHT"]:
                    continue
                return item
        return None

    def checkIsGood(self, item: Item) -> bool:
        # Magics
        if item.type == "MAGIC":
            return True

        # Healers
        if item.attackKind in ["INCREASE_HP", "INCREASE_MP", "REMOVE_ALL_HARMS", "REMOVE_LOWER_HARMS"]:
            return True

        # Goods
        if item.attackExtra in ["SET_ASSISTANT", "INCREASE_ATK", "MAGIC_FREE", "REVIVE", "DYING_ATTACK"]:
            return True

        # Protectors
        if item.defenseKind in ["REFLECT_ANY", "COUNTER"]:
            return True

        return False

    def getMaxMPForMagic(self) -> int:
        maxMP = 0
        for id in self.player.magics:
            item = self.server.itemManager.getItem(id)
            maxMP = max(item.subValue, maxMP)
        for id in self.player.items:
            item = self.server.itemManager.getItem(id)
            if item.type == "MAGIC":
                maxMP = max(item.subValue, maxMP)
        return maxMP

    # Kind of a hack to avoid multiple magics surpassing the mp limit
    def removeExcessMagic(self, items: list[Item]):
        mpCost = 0
        for item in list(items):
            if item.attackExtra == "MAGICAL":
                mpCost = 99
            if item.type == "MAGIC":
                mpCost += item.subValue
                if mpCost > self.player.mp:
                    items.remove(item)

    def onAttackTurn(self) -> AttackData:
        return AttackData(self.player, *self.buildAttack())

    def buildAttack(self) -> tuple[Player, list[Item]]:
        # TODO: Build weighted list with all attack possibilities
        # TODO: Better MP Handling
        # TODO: Help team-mates

        self.checkEnemyStats()

        target = None
        if len(self.possiblyDefenceless) == 0:
            target = self.room.getRandomAliveEnemy(self.player)
        else:
            print("Bot targetting possibly defenceless player.")
            target = random.choice(self.possiblyDefenceless)
        print("Bot target:", target)
        
        random.shuffle(self.player.items) # TODO: don't do this in this way, maybe use a random access iterator or do a copy or smth
        random.shuffle(self.player.magics) # TODO: don't do this in this way, maybe use a random access iterator or do a copy or smth
        pieces = []
        lastResortAttack = None
        specialLastResortAttack = None

        for id in self.player.magics:
            item = self.server.itemManager.getItem(id)

            if self.player.mp < item.subValue:
                continue

            if item.attackKind in ["ATK", "ADD_HARM"]:
                if target.disease == item.attackExtra or item.attackExtra in target.harms:
                    continue
                return target, [item]

            if item.attackExtra in ["WIDE_ATK", "DOUBLE_ATK"] or\
               item.defenseExtra in ["FLICK_MAGIC", "BLOCK_WEAPON"]:
                # These items can't be used here
                continue
            
            if item.attackKind == "SET_ASSISTANT":
                if self.player.assistantType is not None:
                    continue

            if item.attackKind == "INCREASE_HP":
                if lastResortAttack is None:
                    lastResortAttack = self.player, [item]
                if self.player.hp >= 25:
                    continue

            if item.attackKind == "REMOVE_ALL_HARMS":
                if not self.player.disease:
                    continue

            if item.attackKind == "REMOVE_LOWER_HARMS":
                if not self.player.hasLowerDisease():
                    continue

            return self.player, [item]

        for id in self.player.items:
            item = self.server.itemManager.getItem(id)

            if item.type == "SUNDRY":
                if item.attackKind == "SET_ASSISTANT":
                    if self.player.assistantType is not None:
                        continue
                    return self.player, [item]

                if item.attackExtra in ["INCREASE_ATK", "MAGIC_FREE", "REVIVE", "MORTAR"]:
                    # These items can't be used for direct attacks
                    continue

                if item.attackKind == "INCREASE_HP":
                    if lastResortAttack is None:
                        lastResortAttack = self.player, [item]
                    if self.player.hp >= 25:
                        continue
                    return self.player, [item]

                if item.attackKind == "INCREASE_MP":
                    if lastResortAttack is None:
                        lastResortAttack = self.player, [item]
                    if self.player.mp >= self.getMaxMPForMagic():
                        continue
                    return self.player, [item]

                if item.attackKind == "REMOVE_ALL_HARMS":
                    if not self.player.disease:
                        # TODO: Use the item if we need inventory space and don't have a remove lower harms item
                        continue
                    return self.player, [item]

                if item.attackKind == "REMOVE_LOWER_HARMS":
                    if not self.player.hasLowerDisease():
                        # TODO: Use the item if we need inventory space
                        continue
                    return self.player, [item]

                if item.attackKind == "REMOVE_ABILITIES":
                    if len(target.magics) == 0:
                        continue
                
                return target, [item]

            if item.type == "TRADE":
                if item.attackKind == "SELL":
                    # Always try to sell mortars when we have one
                    mortar = self.getItemsByAE("MORTAR")
                    if len(mortar) > 0:
                        return target, [item, mortar[0]]

                    # Try to sell the most valuable item that isn't good
                    # TODO: Sell good items if it can be good for us
                    mostValuable = None
                    for id in self.player.items:
                        _item = self.server.itemManager.getItem(id)
                        if self.checkIsGood(_item):
                            continue
                        if _item not in self.player.magics and _item != item and (mostValuable is None or mostValuable.price < _item.price):
                            mostValuable = _item
                    if mostValuable is not None:
                        if mostValuable.price > 10:
                            return target, [item, mostValuable]
                        if lastResortAttack is None:
                            lastResortAttack = target, [item, mostValuable]
                elif item.attackKind == "BUY":
                    if self.player.yen < 10:
                        continue
                    return target, [item]
                elif item.attackKind == "EXCHANGE":
                    # TODO: NOT IMPLEMENTED
                    continue

            if item.type == "WEAPON":
                if item.attackKind == "ATK":
                    if specialLastResortAttack is None:
                        specialLastResortAttack = target, [item]

                    if item.attackExtra == "PESTLE":
                        return target, [item]

                    if item.attackExtra == "DYING_ATTACK":
                        # Save the dying attack for when we are dying
                        # TODO: Use the dying attack if it can be good for us (hardly this can be possible tho)
                        continue

                    if "REFLECT" in item.defenseExtra or "FLICK" in item.defenseExtra or "BLOCK" in item.defenseExtra:
                        if lastResortAttack is None:
                            lastResortAttack = target, [item]
                        #TODO: Use this item if we need inventory space or if we can kill the enemy
                        continue

                    if item.hitRate > 0:
                        return target, [item]
                    
                    isSpecial = item.attribute in ["DARK", "LIGHT"]
                    # TODO: Try to make it wait to stack a better attack, like with increase_atk and others extras
                    # TODO: Only override item attribute if we can get a good damage doing so
                    # TODO: If weapon or extras has ADD_HARM, try to stack as much damage as possible

                    if item.attackExtra != "WIDE_ATK" and item.attackExtra != "INCREASE_ATK" and item.attackExtra != "DOUBLE_ATK" and item.attackExtra != "ADD_ATTRIBUTE":
                        pieces.append(item)
                        if not isSpecial:
                            pieces += self.getItemsByAE("INCREASE_ATK")
                            damage = self.getItemsDamage(pieces)
                            if damage >= 10:
                                pieces += self.getItemsByAE("DOUBLE_ATK")
                            pieces += self.getItemsByAE("ADD_ATTRIBUTE")
                        else:
                            pieces += self.getItemsByAE("INCREASE_ATK", item.attribute)
                            pieces += self.getItemsByAE("ADD_ATTRIBUTE", item.attribute)
                        self.removeExcessMagic(pieces)
                        damage = self.getItemsDamage(pieces)
                        if damage > 5 and self.room.getAliveCount() > 2:
                            pieces += self.getItemsByAE("WIDE_ATK")
                        self.removeExcessMagic(pieces)
                        return target, pieces

                    if item.attackExtra != "WIDE_ATK" and item.attackExtra != "INCREASE_ATK" and item.attackExtra != "ADD_ATTRIBUTE":
                        pieces.append(item)
                        if not isSpecial:
                            pieces += self.getItemsByAE("INCREASE_ATK")
                            pieces += self.getItemsByAE("ADD_ATTRIBUTE")
                        else:
                            pieces += self.getItemsByAE("INCREASE_ATK", item.attribute)
                            pieces += self.getItemsByAE("ADD_ATTRIBUTE", item.attribute)
                        self.removeExcessMagic(pieces)
                        damage = self.getItemsDamage(pieces)
                        if damage > 5 and self.room.getAliveCount() > 2:
                            pieces += self.getItemsByAE("WIDE_ATK")
                        self.removeExcessMagic(pieces)
                        return target, pieces

                    if item.attackExtra != "INCREASE_ATK" and item.attackExtra != "ADD_ATTRIBUTE":
                        pieces.append(item)
                        if not isSpecial:
                            pieces += self.getItemsByAE("INCREASE_ATK")
                            pieces += self.getItemsByAE("ADD_ATTRIBUTE")
                        else:
                            pieces += self.getItemsByAE("INCREASE_ATK", item.attribute)
                            pieces += self.getItemsByAE("ADD_ATTRIBUTE", item.attribute)
                        self.removeExcessMagic(pieces)
                        return target, pieces

                    if item.attackExtra != "ADD_ATTRIBUTE":
                        pieces.append(item)
                        pieces += self.getItemsByAE("ADD_ATTRIBUTE", item.attribute if isSpecial else None)
                        self.removeExcessMagic(pieces)
                        return target, pieces

                    pieces.append(item)
                    return target, pieces

            if item.type == "MAGIC":
                if self.player.mp < item.subValue:
                    continue

                if item.attackKind == "ATK":
                    return target, [item]

                if item.attackKind == "ADD_HARM":
                    if target.disease == item.attackExtra or item.attackExtra in target.harms:
                        continue
                    return target, [item]

                if item.attackExtra in ["WIDE_ATK", "DOUBLE_ATK"] or\
                   item.defenseExtra in ["FLICK_MAGIC", "BLOCK_WEAPON"]:
                    # These items can't be used here
                    continue
                
                if item.attackKind == "SET_ASSISTANT":
                    if self.player.assistantType is not None:
                        continue

                if item.attackKind == "INCREASE_HP":
                    if lastResortAttack is None:
                        lastResortAttack = self.player, [item]
                    if self.player.hp >= 25:
                        continue

                if item.attackKind == "REMOVE_ALL_HARMS":
                    if not self.player.disease:
                        continue

                if item.attackKind == "REMOVE_LOWER_HARMS":
                    if not self.player.hasLowerDisease():
                        continue

                return self.player, [item]

        if lastResortAttack is not None:
            # We can't do anything else, so we can only resort to this
            return lastResortAttack

        if specialLastResortAttack is not None:
            # We LITERALLY can't do anything else, so we can only resort to this
            return specialLastResortAttack

        return target, [self.server.itemManager.getItem(0)]

    def onDefenseTurn(self):
        assert(self.room.turn.currentAttack is not None)
        
        # TODO: Build weighted list with all defense possibilities
        # TODO: Better MP Handling
        
        ret = []

        damage, attr = self.room.turn.currentAttack.damage, self.room.turn.currentAttack.attribute
        print("Damage:", damage, "| Attr:", attr)

        if damage <= 0:
            # TODO: Try to reflect, flick or block
            return ret

        protectors = self.getDefenseItems(attr) if attr is not None else []
        isCounter = self.room.turn.currentAttack.piece[0].defenseKind == "COUNTER"
        isMagic = self.room.turn.currentAttack.piece[0].type == "MAGIC"
        isWeapon = self.room.turn.currentAttack.piece[0].type == "WEAPON"
        counter = self.getCounterItem(attr, isCounter, isMagic, isWeapon)

        isBlock = False
        if counter:
            isBlock = "REFLECT" in counter.defenseExtra or "FLICK" in counter.defenseExtra or "BLOCK" in counter.defenseExtra

        attrRemoved = False
        if "GLORY" not in self.player.harms and attr and self.player.hasItem(195) and not protectors and not counter:
            protectors_ne = self.getDefenseItems("")
            counter_ne = self.getCounterItem("", isCounter, isMagic, isWeapon)
            if protectors_ne or counter_ne:
                # We can use NE protectors or counters, so lets erase the attribute with the wings.
                protectors = protectors_ne
                counter = counter_ne
                attr = ""
                attrRemoved = True
                ret.append(self.server.itemManager.getItem(195))

        if counter and (damage >= 15 or self.room.turn.currentAttack.attacker.hp <= damage or any(i.isAtkHarm() for i in self.room.turn.currentAttack.piece)):
            ret.append(counter)
            return ret

        if isCounter:
            # This is a counter-attack so ignore defense items
            return ret

        defPiece = []
        if attr is not None:
            for p in protectors:
                defPiece.append(p)
                damage -= p.getDef()

                if damage <= 0:
                    break

            if damage > 2 or (self.player.hp < 30 and damage > 0):
                rings = self.getCounterRings(attr)
                defPiece += rings

        if len(ret) == (1 if attrRemoved else 0) and counter and (damage >= 5 or self.player.hp <= 15 or self.player.hp <= damage or any(i.isAtkHarm() for i in self.room.turn.currentAttack.piece)):
            ret.append(counter)
            return ret
        
        ret += defPiece

        if len(ret) > 1 and "GLORY" in self.player.harms:
            ret = ret[1:2] if ret[0].id == 195 else ret[:1]

        return ret

    def getBuyResponse(self, decidedItem) -> bool:
        # TODO.
        return True

    def notifyAttack(self, atkData, defPiece, blocked):
        attacker = atkData.attacker
        defender = atkData.defender

        stats = None
        if attacker.name not in self.enemyStats:
            stats = EnemyStats()
            self.enemyStats[attacker.name] = stats
        else:
            stats = self.enemyStats[attacker.name]

    def notifyItemDiscard(self, player, itemId):
        pass

    def notifyMagicDiscard(self, player, itemId):
        stats = None
        if player.name not in self.enemyStats:
            stats = EnemyStats()
            self.enemyStats[player.name] = stats
        else:
            stats = self.enemyStats[player.name]