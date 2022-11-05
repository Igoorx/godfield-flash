from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Iterator
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
                if stats.lastHP - player.hp > 2:
                    # Took damage
                    stats.damageCombo += 1

                    if stats.damageCombo > 1 and not player in self.possiblyDefenceless:
                        # Possibly defenseless
                        self.possiblyDefenceless.append(player)
                elif stats.lastHP <= player.hp:
                    # Didn't take damage
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
        return sorted(items, key = lambda x: x.getDef())

    def getCounterRings(self, forAttribute: str) -> list[Item]:
        items = []
        harms = []
        for id in self.player.items:
            item = self.server.itemManager.getItem(id)

            if item.defenseKind == "COUNTER" and not (item.isAtkHarm() and item.attackExtra in harms):
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
                if item.isAtkHarm():
                    harms.append(item.attackExtra)
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
                if forAttribute is None or counter:
                    continue
                elif "WEAPON" in item.defenseExtra:
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
                if forAttribute is None or counter:
                    continue
                elif "WEAPON" in item.defenseExtra:
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

    def getMaxMPForMagic(self, target: Player) -> int:
        maxMP = 0
        for id in target.magics:
            item = self.server.itemManager.getItem(id)
            maxMP = max(item.subValue, maxMP)
        for id in target.items:
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

    def getAllies(self) -> Iterator[Player]:
        yield self.player
        if self.player.team != "SINGLE":
            for player in self.room.players:
                if player != self.player and not player.dead and not player.isEnemy(self.player):
                    yield player

    def getKillableEnemy(self, item: Item, overrideDamage: Optional[int] = None) -> Player:
        if not item.attribute:
            return None
        for player in self.room.players:
            if not player.dead and player.hp <= (item.getAtk() if overrideDamage is None else overrideDamage) and player.isEnemy(self.player):
                return player
        return None

    def onAttackTurn(self) -> AttackData:
        newAttack = AttackData(self.player, *self.buildAttack())
        if newAttack.piece[0].attackKind == "EXCHANGE":
            newAttack.decidedExchange = self.buildExchange()
        return newAttack

    def buildAttack(self) -> tuple[Player, list[Item]]:
        # TODO: Build weighted list with all attack possibilities
        # TODO: Better MP Handling

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
        possibleDiscard = []
        lastResortAttack = None
        specialLastResortAttack = None
        
        for id in self.player.magics:
            item = self.server.itemManager.getItem(id)

            if self.player.mp < item.subValue:
                continue

            # Avoid spamming magics with a low hit rate.
            if 0 < item.hitRate < random.randrange(1, 100 + 1):
                continue

            if item.attackKind == "ATK":
                killableEnemy = self.getKillableEnemy(item)
                return target if killableEnemy is None else killableEnemy, [item]

            if item.attackKind == "ADD_HARM":
                if target.disease == item.attackExtra or item.attackExtra in target.harms:
                    continue
                return target, [item]

            if item.attackExtra in ["WIDE_ATK", "DOUBLE_ATK"] or\
               item.defenseExtra in ["FLICK_MAGIC", "BLOCK_WEAPON"]:
                # These items can't be used here
                continue
            
            if item.attackKind == "SET_ASSISTANT":
                for ally in self.getAllies():
                    if ally.assistantType:
                        continue
                    return ally, [item]

            if item.attackKind == "INCREASE_HP":
                if lastResortAttack is None:
                    lastResortAttack = self.player, [item]
                for ally in self.getAllies():
                    if ally.hp >= 25:
                        continue
                    return ally, [item]

            if item.attackKind == "INCREASE_YEN":
                if specialLastResortAttack is None:
                    specialLastResortAttack = self.player, [item]
                if self.player.yen >= 50:
                    continue
                return self.player, [item]

            if item.attackKind == "REMOVE_ALL_HARMS":
                if specialLastResortAttack is None:
                    specialLastResortAttack = self.player, [item]
                for ally in self.getAllies():
                    if not ally.disease:
                        continue
                    return ally, [item]

            if item.attackKind == "REMOVE_LOWER_HARMS":
                if specialLastResortAttack is None:
                    specialLastResortAttack = self.player, [item]
                for ally in self.getAllies():
                    if not ally.hasLowerDisease():
                        continue
                    return ally, [item]

        for id in self.player.items:
            item = self.server.itemManager.getItem(id)

            if item.type == "SUNDRY":
                if item.attackExtra not in ["MORTAR", "REMOVE_ABILITIES", "REVIVE"]:
                    possibleDiscard.append(item)

                if item.attackExtra in ["INCREASE_ATK", "MAGIC_FREE", "REVIVE", "MORTAR"]:
                    # These items can't be used for direct attacks
                    continue

                if item.attackKind == "SET_ASSISTANT":
                    for ally in self.getAllies():
                        if ally.assistantType:
                            continue
                        return ally, [item]
                    # No allies need this item, so skip it for now.
                    continue

                if item.attackKind == "INCREASE_HP":
                    if lastResortAttack is None:
                        lastResortAttack = self.player, [item]
                    for ally in self.getAllies():
                        if ally.hp >= 25:
                            continue
                        return ally, [item]
                    # No allies need this item, so skip it for now.
                    continue

                if item.attackKind == "INCREASE_MP":
                    if lastResortAttack is None:
                        lastResortAttack = self.player, [item]
                    for ally in self.getAllies():
                        if ally.mp >= self.getMaxMPForMagic(ally):
                            continue
                        return ally, [item]
                    # No allies need this item, so skip it for now.
                    continue

                if item.attackKind == "REMOVE_ALL_HARMS":
                    for ally in self.getAllies():
                        if not ally.disease:
                            # TODO: Use the item if we need inventory space and don't have a remove lower harms item
                            continue
                        return ally, [item]
                    # No allies need this item, so skip it for now.
                    continue

                if item.attackKind == "REMOVE_LOWER_HARMS":
                    for ally in self.getAllies():
                        if not ally.hasLowerDisease():
                            # TODO: Use the item if we need inventory space
                            continue
                        return ally, [item]
                    # No allies need this item, so skip it for now.
                    continue

                if item.attackKind == "REMOVE_ABILITIES":
                    if len(target.magics) == 0:
                        continue
                
                return target, [item]

            elif item.type == "TRADE":
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
                    if self.player.yen == 0:
                        possibleDiscard.append(item)
                        continue
                    elif self.player.yen < 5:
                        if lastResortAttack is None:
                            lastResortAttack = target, [item]
                        continue
                    return target, [item]
                elif item.attackKind == "EXCHANGE":
                    possibleDiscard.append(item)
                    if self.player.hp <= 30 and self.player.mp == 0 and self.player.yen == 0:
                        # Exchange would result in "No Change"
                        continue
                    needsHP = self.player.hp < 20
                    needsMP = self.player.mp < 30 and (self.player.magics or any(self.server.itemManager.getItem(id).type == "MAGIC" for item in self.player.items))
                    if needsHP or (needsMP and (self.player.yen > 0 or self.player.hp >= 50)):
                        return self.player, [item]

            elif item.type == "WEAPON":
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
                        killableEnemy = self.getKillableEnemy(item, damage)
                        return target if killableEnemy is None else killableEnemy, pieces

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
                        killableEnemy = self.getKillableEnemy(item)
                        return target if killableEnemy is None else killableEnemy, pieces

                    if item.attackExtra != "INCREASE_ATK" and item.attackExtra != "ADD_ATTRIBUTE":
                        pieces.append(item)
                        if not isSpecial:
                            pieces += self.getItemsByAE("INCREASE_ATK")
                            pieces += self.getItemsByAE("ADD_ATTRIBUTE")
                        else:
                            pieces += self.getItemsByAE("INCREASE_ATK", item.attribute)
                            pieces += self.getItemsByAE("ADD_ATTRIBUTE", item.attribute)
                        self.removeExcessMagic(pieces)
                        killableEnemy = self.getKillableEnemy(item)
                        return target if killableEnemy is None else killableEnemy, pieces

                    if item.attackExtra != "ADD_ATTRIBUTE":
                        pieces.append(item)
                        pieces += self.getItemsByAE("ADD_ATTRIBUTE", item.attribute if isSpecial else None)
                        self.removeExcessMagic(pieces)
                        killableEnemy = self.getKillableEnemy(item)
                        return target if killableEnemy is None else killableEnemy, pieces

                    pieces.append(item)
                    killableEnemy = self.getKillableEnemy(item)
                    return target if killableEnemy is None else killableEnemy, pieces

            elif item.type == "MAGIC":
                if self.player.mp < item.subValue:
                    continue

                if item.attackKind == "ATK":
                    killableEnemy = self.getKillableEnemy(item)
                    return target if killableEnemy is None else killableEnemy, [item]

                if item.attackKind == "ADD_HARM":
                    if target.disease == item.attackExtra or item.attackExtra in target.harms:
                        continue
                    return target, [item]

                if item.attackExtra in ["WIDE_ATK", "DOUBLE_ATK"] or\
                   item.defenseExtra in ["FLICK_MAGIC", "BLOCK_WEAPON"]:
                    # These items can't be used here
                    continue
                
                if item.attackKind == "SET_ASSISTANT":
                    for ally in self.getAllies():
                        if ally.assistantType:
                            continue
                        return ally, [item]

                if item.attackKind == "INCREASE_HP":
                    if lastResortAttack is None:
                        lastResortAttack = self.player, [item]
                    for ally in self.getAllies():
                        if ally.hp >= 25:
                            continue
                        return ally, [item]

                if item.attackKind == "REMOVE_ALL_HARMS":
                    for ally in self.getAllies():
                        if not ally.disease:
                            continue
                        return ally, [item]

                if item.attackKind == "REMOVE_LOWER_HARMS":
                    for ally in self.getAllies():
                        if not ally.hasLowerDisease():
                            continue
                        return ally, [item]

            elif item.type == "PROTECTOR":
                if item.defenseExtra != "REFLECT_ANY":
                    possibleDiscard.append(item)

        if lastResortAttack is not None:
            # We can't do anything else, so we can only resort to this
            return lastResortAttack

        if len(self.player.items) == 16 and len(possibleDiscard) != 0:
            # Discard two items so we can receive new items in the next turn.
            return self.player, [self.server.itemManager.getItem(1)] + random.sample(possibleDiscard, k = min(2, len(possibleDiscard)))

        if specialLastResortAttack is not None:
            # We LITERALLY can't do anything else, so we can only resort to this
            return specialLastResortAttack

        print(f"Bot \"{self.player.name}\" couldn't do anything with it's current items.")
        print(list(map(self.server.itemManager.getItem, self.player.items)))

        return target, [self.server.itemManager.getItem(0)]

    def buildExchange(self) -> dict[str, int]:
        decidedExchange = {
            "HP": 0,
            "MP": 0,
            "YEN": 0
        }
        sum = self.player.hp + self.player.mp + self.player.yen

        decidedExchange["HP"] = 30
        sum -= 30
        if sum < 0:
            decidedExchange["HP"] -= sum * -1
            return decidedExchange

        decidedExchange["MP"] = 30
        sum -= 30
        if sum < 0:
            decidedExchange["MP"] -= sum * -1
            return decidedExchange

        decidedExchange["YEN"] = 20
        sum -= 20
        if sum < 0:
            decidedExchange["YEN"] -= sum * -1
            return decidedExchange

        decidedExchange["HP"] += sum
        sum = 0
        if decidedExchange["HP"] > 99:
            sum = decidedExchange["HP"] - 99
            decidedExchange["HP"] = 99

        decidedExchange["MP"] += sum
        assert decidedExchange["MP"] <= 99
        return decidedExchange

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

        isCounter = self.room.turn.currentAttack.piece[0].defenseKind == "COUNTER"
        isMagic = self.room.turn.currentAttack.piece[0].type == "MAGIC"
        isWeapon = self.room.turn.currentAttack.piece[0].type == "WEAPON"

        protectors = self.getDefenseItems(attr) if attr is not None else []
        counter = self.getCounterItem(attr, isCounter, isMagic, isWeapon)

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
                if attr != "DARK" and p.getDef() > 5:
                    if self.player.hp >= 30 and damage / p.getDef() < 0.5:
                        # Not worth it.
                        continue
                    if self.player.hp > damage and damage / p.getDef() <= 0.4:
                        # Not worth it.
                        continue
                defPiece.append(p)
                damage -= p.getDef()

                if damage <= 0:
                    break

            if self.player.hp <= damage:
                # We will die, so let's maximize counter efficiency
                defPiece = self.getCounterRings(attr)
            elif damage > 2 or (self.player.hp < 30 and damage > 0):
                rings = self.getCounterRings(attr)
                defPiece += rings

        if len(ret) == (1 if attrRemoved else 0) and counter and (damage >= 5 or self.player.hp <= 15 or self.player.hp <= damage or any(i.isAtkHarm() for i in self.room.turn.currentAttack.piece)):
            ret.append(counter)
            return ret
        
        ret += defPiece

        if len(ret) == 1 and attr != "DARK" and ret[0].id == 195:
            ret = []
        elif len(ret) > 1 and "GLORY" in self.player.harms:
            ret = ([] if attr != "DARK" else ret[:1]) if ret[0].id == 195 else ret[-1:]

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

    def notifyMagicDiscard(self, player, itemId):
        stats = None
        if player.name not in self.enemyStats:
            stats = EnemyStats()
            self.enemyStats[player.name] = stats
        else:
            stats = self.enemyStats[player.name]