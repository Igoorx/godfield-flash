from helpers.xmlbuilder import XMLBuilder
from modules.game.player import Player

import random


class Bot(Player):
    def __init__(self, name, team):
        Player.__init__(self, None, name, team)

    def getItemByAK(self, kind):
        for id in self.items:
            item = self.server.itemManager.getItem(id)

            if item.type == "MAGIC" and self.mp < item.subValue:
                continue
            if item.attackKind == kind:
                return item
        return None

    def getItemsByAE(self, extra):
        items = []
        for id in self.items:
            item = self.server.itemManager.getItem(id)

            if item.type == "MAGIC" and self.mp < item.subValue:
                continue
            if item.attackExtra == extra:
                items.append(item)
        return items

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

    def getCounterItem(self, forAttribute, counter):
        for id in self.items:
            item = self.server.itemManager.getItem(id)

            if "REFLECT" in item.defenseExtra or\
               "FLICK" in item.defenseExtra or\
               "BLOCK" in item.defenseExtra:
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

    def on_turn(self):
        target = random.choice([player for player in self.room.players if not player.dead and player != self])
        print "Bot target:", target

        random.shuffle(self.items)

        pieces = []
        isAttack = False
        isAction = False
        isSundry = False

        for id in self.items:
            item = self.server.itemManager.getItem(id)

            if item.type == "SUNDRY":
                if item.attackKind == "SET_ASSISTANT":
                    continue

                if item.attackExtra == "INCREASE_ATK" or\
                   item.attackExtra == "MAGIC_FREE" or\
                   item.attackExtra == "REVIVE" or\
                   item.attackExtra == "MORTAR":
                    continue

                if item.attackKind in ["INCREASE_HP", "INCREASE_MP", "REMOVE_ALL_HARMS", "REMOVE_LOWER_HARMS"]:
                    return self, [item]
                else:
                    return target, [item]

            if item.type == "TRADE":
                if item.attackKind == "SELL":
                    mortar = self.getItemsByAE("MORTAR")
                    if mortar:
                        return target, [item, mortar[0]]

                    mostValuable = None
                    for id in self.items:
                        _item = self.server.itemManager.getItem(id)
                        if _item not in self.magics and _item != item and (mostValuable is None or mostValuable.price < _item.price):
                            mostValuable = _item
                    if mostValuable is not None:
                        return target, [item, mostValuable]
                elif item.attackKind == "BUY":
                    return target, [item]

            if item.type == "WEAPON":
                if item.attackKind == "ATK":
                    if item.attackExtra == "DYING_ATTACK":
                        continue

                    if item.hitRate > 0 and not isAttack and not isAction and not isSundry:
                        return target, [item]

                    if item.attackExtra != "WIDE_ATK" and item.attackExtra != "INCREASE_ATK" and item.attackExtra != "DOUBLE_ATK" and item.attackExtra != "ADD_ATTRIBUTE" and\
                       not isAttack and not isAction and not isSundry:
                        isAttack = True
                        pieces.append(item)
                        pieces += self.getItemsByAE("INCREASE_ATK")
                        if item.getAD()[0] >= 10:
                            pieces += self.getItemsByAE("DOUBLE_ATK")
                        pieces += self.getItemsByAE("ADD_ATTRIBUTE")
                        if item.getAD()[0] >= 5:
                            pieces += self.getItemsByAE("WIDE_ATK")
                        return target, pieces

                    if item.attackExtra != "WIDE_ATK" and item.attackExtra != "INCREASE_ATK" and item.attackExtra != "ADD_ATTRIBUTE" and\
                       not isAttack and not isAction and not isSundry:
                        isAttack = True
                        pieces.append(item)
                        pieces += self.getItemsByAE("INCREASE_ATK")
                        pieces += self.getItemsByAE("ADD_ATTRIBUTE")
                        if item.getAD()[0] >= 5:
                            pieces += self.getItemsByAE("WIDE_ATK")
                        return target, pieces

                    if item.attackExtra != "INCREASE_ATK" and item.attackExtra != "ADD_ATTRIBUTE" and\
                       not isAttack and not isAction and not isSundry:
                        isAttack = True
                        pieces.append(item)
                        pieces += self.getItemsByAE("INCREASE_ATK")
                        pieces += self.getItemsByAE("ADD_ATTRIBUTE")
                        return target, pieces

                    if item.attackExtra != "ADD_ATTRIBUTE" and\
                       not isAttack and not isAction and not isSundry:
                        sAttack = True
                        pieces.append(item)
                        pieces += self.getItemsByAE("ADD_ATTRIBUTE")
                        return target, pieces

                    if not isAttack and not isAction and not isSundry:
                        sAttack = True
                        pieces.append(item)
                        return target, pieces

            if item.type == "MAGIC":
                if self.mp < item.subValue:
                    continue

                if item.attackKind in ["ATK", "ADD_HARM"]:
                    if not isAttack and not isAction and not isSundry:
                        sAttack = True
                        pieces.append(item)
                        return target, pieces

        return target, [self.server.itemManager.getItem(0)]

    def on_attack(self):
        ret = []

        damage, attr = self.room.turn.currentAttack.damage, self.room.turn.currentAttack.attribute
        print damage, attr

        if damage <= 0:
            return []

        isCounter = self.room.turn.currentAttack.piece[0].defenseKind == "COUNTER"

        attrBkp = None
        if "GLORY" not in self.harms and attr and self.hasItem(195):
            attrBkp = attr
            attr = ""
            ret.append(self.server.itemManager.getItem(195))

        if damage >= 15 or self.room.turn.currentAttack.attacker.hp <= damage or any(i.isAtkHarm() for i in self.room.turn.currentAttack.piece):
            counter = self.getCounterItem(attr, isCounter)

            if counter:
                if not ("WEAPON" in counter.defenseExtra and not self.room.turn.currentAttack.piece[0].type == "WEAPON") and\
                   not ("MAGIC" in counter.defenseExtra and not self.room.turn.currentAttack.piece[0].type == "MAGIC"):
                    ret.append(counter)
                    return ret

        if isCounter:
            return ret

        if attr is not None:
            protectors = self.getDefenseItems(attr)

            for p in protectors:
                a, d = p.getAD()
                ret.append(p)
                damage -= d

                if damage <= 0:
                    break

            if damage > 0:
                rings = self.getCounterRings(attr)
                ret += rings

        if len(ret) == 1 and ret[0].id == 195:
            attr = attrBkp
            ret = []

        if len(ret) == 0 and (damage >= 5 or self.hp <= 10 or self.hp <= damage or any(i.isAtkHarm() for i in self.room.turn.currentAttack.piece)):
            counter = self.getCounterItem(attr, isCounter)

            if counter:
                if not ("WEAPON" in counter.defenseExtra and not self.room.turn.currentAttack.piece[0].type == "WEAPON") and \
                   not ("MAGIC" in counter.defenseExtra and not self.room.turn.currentAttack.piece[0].type == "MAGIC"):
                    ret.append(counter)
                    return ret

        if len(ret) > 1 and "GLORY" in self.harms:
            ret = ret[:1]

        return ret
