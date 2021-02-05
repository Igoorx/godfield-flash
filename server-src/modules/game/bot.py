from helpers.xmlbuilder import XMLBuilder
from modules.game.player import Player

import random

class EnemyStats:
    def __init__(self):
        self.lastHP = None
        self.lastDiseases = None
        self.damageCombo = 0

class Bot(Player):
    def __init__(self, name, team):
        Player.__init__(self, None, name, team)

        self.enemyStats = dict()
        self.possiblyDefenceless = list()

    def checkEnemyStats(self):
        for player in self.room.players:
            if player == self:
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

            lastHP = stats.lastHP
            if lastHP > player.hp:
                # Took damage
                stats.damageCombo += 1

                if stats.damageCombo > 1 and not player in self.possiblyDefenceless:
                    # Possibly defenseless
                    self.possiblyDefenceless.append(player)
            elif lastHP <= player.hp:
                # Didn't took damage
                stats.damageCombo = 0

            stats.lastHP = player.hp

        print(self.enemyStats)
            

    def getItemByAK(self, kind):
        for id in self.items:
            item = self.server.itemManager.getItem(id)

            if item.type == "MAGIC" and self.mp < item.subValue:
                continue
            if item.attackKind == kind:
                return item
        return None

    def getItemsByAE(self, extra, attr = None):
        items = []
        for id in self.items:
            item = self.server.itemManager.getItem(id)

            if item.type == "MAGIC" and self.mp < item.subValue:
                continue
            if attr is not None and item.attribute != attr:
                continue
            if item.attackExtra == extra:
                items.append(item)
        for id in self.magics:
            item = self.server.itemManager.getItem(id)
            
            if self.mp < item.subValue:
                continue
            if attr is not None and item.attribute != attr:
                continue
            if item.attackExtra == extra:
                items.append(item)
        return items

    def getItemsDamage(self, items):
        damage = 0
        for item in items:
            if item.attackExtra == "DOUBLE_ATK":
                damage *= 2
            else:
                damage += item.getAD()[0]
        return damage

    def getDefenseItems(self, forAttribute):
        items = []
        for id in self.items:
            item = self.server.itemManager.getItem(id)

            if item.defenseKind == "DFS":
                if item.type == "MAGIC" and self.mp < item.subValue:
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
        for id in self.magics:
            item = self.server.itemManager.getItem(id)

            if self.mp < item.subValue:
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

    def getCounterRings(self, forAttribute):
        items = []
        for id in self.items:
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

    def getCounterItem(self, forAttribute, counter, magic, weapon):
        for id in self.items:
            item = self.server.itemManager.getItem(id)

            if "REFLECT" in item.defenseExtra or\
               "FLICK" in item.defenseExtra or\
               "BLOCK" in item.defenseExtra:
                if ("MAGIC" in item.defenseExtra and not magic) or\
                   ("WEAPON" in item.defenseExtra and not weapon):
                    continue
                if item.type == "MAGIC" and self.mp < item.subValue:
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
        for id in self.magics:
            item = self.server.itemManager.getItem(id)

            if self.mp < item.subValue:
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

    def checkIsGood(self, item):
        # Healers
        if item.attackKind in ["INCREASE_HP", "INCREASE_MP", "REMOVE_ALL_HARMS", "REMOVE_LOWER_HARMS"]:
            return True

        # Goods
        if item.attackExtra in ["SET_ASSISTANT", "INCREASE_ATK", "MAGIC_FREE", "REVIVE", "DYING_ATTACK"]:
            return True

        # Protectors
        if item.defenseKind in ["REFLECT_ANY"]:
            return True

        return False

    def getMaxMPForMagic(self):
        max = 0
        for id in self.magics:
            item = self.server.itemManager.getItem(id)
            max = item.subValue if item.subValue > max else max
        for id in self.items:
            item = self.server.itemManager.getItem(id)
            if item.type == "MAGIC":
                max = item.subValue if item.subValue > max else max
        return max

    # Kind of a hack to avoid multiple magics surpassing the mp limit
    def removeExcessMagic(self, items):
        mpCost = 0
        for item in list(items):
            if item.type == "MAGIC":
                mpCost += item.subValue
                if mpCost > self.mp:
                    items.remove(item)

    def on_turn(self):
        # TODO: Build weighted list with all attack possibilities
        # TODO: Better MP Handling

        self.checkEnemyStats()

        target = None
        if len(self.possiblyDefenceless) == 0:
            target = random.choice([player for player in self.room.players if not player.dead and player != self])
        else:
            print "Bot targetting possibly defenceless player."
            target = random.choice(self.possiblyDefenceless)
        print "Bot target:", target
        
        random.shuffle(self.items)
        random.shuffle(self.magics)
        pieces = []
        lastResortAttack = None

        for id in self.magics:
            item = self.server.itemManager.getItem(id)

            if self.mp < item.subValue:
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
                # TODO: Not Implemented
                continue

            if item.attackKind == "INCREASE_HP":
                if lastResortAttack is None:
                    lastResortAttack = self, [item]
                if self.hp >= 25:
                    continue

            if item.attackKind == "REMOVE_ALL_HARMS":
                if not self.disease:
                    continue

            if item.attackKind == "REMOVE_LOWER_HARMS":
                if not self.hasLowerDisease():
                    continue

            return self, [item]

        for id in self.items:
            item = self.server.itemManager.getItem(id)

            if item.type == "SUNDRY":
                if item.attackKind == "SET_ASSISTANT":
                    # TODO: Not Implemented
                    continue

                if item.attackExtra in ["INCREASE_ATK", "MAGIC_FREE", "REVIVE", "MORTAR"]:
                    # These items can't be used for direct attacks
                    continue

                if item.attackKind == "INCREASE_HP":
                    if lastResortAttack is None:
                        lastResortAttack = self, [item]
                    if self.hp >= 25:
                        continue
                    return self, [item]

                if item.attackKind == "INCREASE_MP":
                    if lastResortAttack is None:
                        lastResortAttack = self, [item]
                    if self.mp >= self.getMaxMPForMagic():
                        continue
                    return self, [item]

                if item.attackKind == "REMOVE_ALL_HARMS":
                    if not self.disease:
                        # TODO: Use the item if we need inventory space and don't have a remove lower harms item
                        continue
                    return self, [item]

                if item.attackKind == "REMOVE_LOWER_HARMS":
                    if not self.hasLowerDisease():
                        # TODO: Use the item if we need inventory space
                        continue
                    return self, [item]

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
                    for id in self.items:
                        _item = self.server.itemManager.getItem(id)
                        if self.checkIsGood(_item):
                            continue
                        if _item not in self.magics and _item != item and (mostValuable is None or mostValuable.price < _item.price):
                            mostValuable = _item
                    if mostValuable is not None:
                        if mostValuable.price > 10:
                            return target, [item, mostValuable]
                        if lastResortAttack is None:
                            lastResortAttack = target, [item, mostValuable]
                elif item.attackKind == "BUY":
                    if self.yen < 10:
                        continue
                    return target, [item]

            if item.type == "WEAPON":
                if item.attackKind == "ATK":
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
                        if damage > 5:
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
                        if damage > 5:
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
                if self.mp < item.subValue:
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
                    # TODO: Not Implemented
                    continue

                if item.attackKind == "INCREASE_HP":
                    if lastResortAttack is None:
                        lastResortAttack = self, [item]
                    if self.hp >= 25:
                        continue

                if item.attackKind == "REMOVE_ALL_HARMS":
                    if not self.disease:
                        continue

                if item.attackKind == "REMOVE_LOWER_HARMS":
                    if not self.hasLowerDisease():
                        continue

                return self, [item]

        if lastResortAttack is not None:
            # We can't do anything else, so we can only resort to this
            return lastResortAttack

        return target, [self.server.itemManager.getItem(0)]

    def on_attack(self):
        # TODO: Build weighted list with all defense possibilities
        # TODO: Better MP Handling
        
        ret = []

        damage, attr = self.room.turn.currentAttack.damage, self.room.turn.currentAttack.attribute
        print damage, attr

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
        if "GLORY" not in self.harms and attr and self.hasItem(195) and not protectors and not counter:
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
                a, d = p.getAD()
                defPiece.append(p)
                damage -= d

                if damage <= 0:
                    break

            if damage > 2 or (self.hp < 30 and damage > 0):
                rings = self.getCounterRings(attr)
                defPiece += rings

        if len(ret) == (1 if attrRemoved else 0) and counter and (damage >= 5 or self.hp <= 15 or self.hp <= damage or any(i.isAtkHarm() for i in self.room.turn.currentAttack.piece)):
            ret.append(counter)
            return ret
        
        ret += defPiece

        if len(ret) > 1 and "GLORY" in self.harms:
            ret = ret[1:2] if ret[0].id == 195 else ret[:1]

        return ret

    def notify_attack(self, atkData, defPiece, blocked):
        attacker = atkData.attacker
        defender = atkData.defender

        stats = None
        if attacker.name not in self.enemyStats:
            stats = EnemyStats()
            self.enemyStats[attacker.name] = stats
        else:
            stats = self.enemyStats[attacker.name]

    def notify_item_discard(self, player, itemId):
        pass

    def notify_magic_discard(self, player, itemId):
        stats = None
        if player.name not in self.enemyStats:
            stats = EnemyStats()
            self.enemyStats[player.name] = stats
        else:
            stats = self.enemyStats[player.name]