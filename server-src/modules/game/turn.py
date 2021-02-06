from helpers.xmlbuilder import XMLBuilder
from modules.game.bot import Bot

import random
from Queue import Queue


class AttackData:
    def __init__(self):
        self.attacker = None
        self.defender = None
        
        self.isAction = bool()
        self.isLast = bool()
        self.isCounter = bool()
        self.isRetargeted = bool()
        
        self.damage = int()
        self.chance = int()
        self.extra = list()
        self.attribute = None
        self.piece = list()

        self.decidedValue = None
        self.decidedHP = None
        self.decidedMystery = None

    def __str__(self):
        return "Attacker: {attacker}, Defender: {defender}, Damage: {attack}, Extra: {extra}, Attribute: {attr}"\
               .format(attacker=self.attacker, defender=self.defender, attack=self.damage, extra=self.extra, attr=self.attribute)

    def copy(self):
        copy = AttackData()
        copy.attacker = self.attacker
        copy.defender = self.defender

        copy.isAction = self.isAction
        copy.isLast = self.isLast
        copy.isCounter = self.isCounter
        copy.isRetargeted = self.isRetargeted
        
        copy.damage = self.damage
        copy.chance = self.chance
        copy.extra = self.extra
        copy.attribute = self.attribute
        copy.piece = self.piece

        copy.decidedValue = self.decidedValue
        copy.decidedHP = self.decidedHP
        copy.decidedMystery = self.decidedMystery
        return copy

class TurnHandler:
    def __init__(self, room):
        self.room = room
        self.server = room.server
        
        self.new()

    def new(self):
        self.currentAttack = None
        self.attackQueue = Queue()

        self.attacker = None
        
        self.buyOportunity = None
        self.sellingItem = None

    def playerDyingAttack(self, player, item):
        builder = XMLBuilder("DYING")
        builder.piece.item(str(item.id))
        self.room.broadXml(builder)

        if item.attackExtra == "REVIVE":
            print "REVIVE"
            player.discardItem(item.id)
            player.hp += item.value
        else:
            print "DYING ATTACK"
            player.dead = True
            builder = XMLBuilder("DIE")
            builder.player.name(player.name)
            self.room.broadXml(builder)
            
            self.newAttack(player, player, [item], 30)

    def playerBuyResponse(self, player, response):
        atkData = self.currentAttack
        print "Buy response: ", self.buyOportunity.id, player, response
        print player == atkData.attacker, self.buyOportunity is not None, atkData.defender.hasItem(self.buyOportunity.id)
        if player == atkData.attacker and self.buyOportunity is not None and atkData.defender.hasItem(self.buyOportunity.id):
            builder = XMLBuilder("BUY")
            
            if response and atkData.attacker.yen >= self.buyOportunity.price:
                builder.doBuy
                atkData.defender.discardItem(self.buyOportunity.id)
                atkData.defender.yen += self.buyOportunity.price
                atkData.attacker.dealItem(self.buyOportunity.id, True)
                atkData.attacker.yen -= self.buyOportunity.price
                
            self.room.broadXml(builder)

    def forceItemBuy(self, seller, target, piece):
        if seller.hasItem(piece.id):
            seller.discardItem(piece.id)
            seller.yen += piece.price
            
            target.dealItem(piece.id, True)
            target.yen -= piece.price
            if target.yen < 0:
                target.mp -= target.yen * -1
                target.yen = 0
                if target.mp < 0:
                    target.hp = max(0, target.hp - target.mp * -1)
                    target.mp = 0

    def canDefendAttr(self, attackAttr, defenseAttr):
        if not attackAttr or attackAttr == "DARK":
            return True
        if not defenseAttr:
            return attackAttr == "DARK"
        if attackAttr == "FIRE":
            return defenseAttr in ["WATER", "LIGHT"]
        elif attackAttr == "WATER":
            return defenseAttr in ["FIRE", "LIGHT"]
        elif attackAttr == "TREE":
            return defenseAttr in ["SOIL", "LIGHT"]
        elif attackAttr == "SOIL":
            return defenseAttr in ["TREE", "LIGHT"]
        elif attackAttr == "LIGHT":
            return defenseAttr == "DARK"
        assert False, "Unknown attribute!"

    def newAttack(self, attacker, defender, piece, decidedValue=None, forced=False, counter=False):
        # TODO: Divide attack handing in different classes, like CommandChain, AttackCommand, Attribute and etc...

        atkData = AttackData()
        atkData.attacker = attacker
        atkData.piece = piece
        atkData.decidedValue = decidedValue
        atkData.isCounter = counter

        massiveAttack = False
        isMagicFree = False if len(piece) == 0 else atkData.piece[-1].attackExtra == "MAGIC_FREE"
        isFirstPiece = True
        
        for item in atkData.piece:
            if not forced:
                if isFirstPiece:
                    isInvalidItem = item.type == "PROTECTOR" or (item.type in ["MAGIC", "SUNDRY"] and not item.attackKind)
                    print(item.__dict__)
                    assert not isInvalidItem, "Invalid attack used!"
                else:
                    isValidItem = item.attackKind not in ["DO_NOTHING", "DISCARD", "SELL", "EXCHANGE", "MYSTERY"] and\
                                    ((item.attackExtra in ["INCREASE_ATK", "DOUBLE_ATK", "WIDE_ATK", "ADD_ATTRIBUTE"] and\
                                      atkData.piece[0].type == "WEAPON" and atkData.piece[0].hitRate == 0) or\
                                        (item.attackExtra == "MAGIC_FREE" and atkData.piece[-1].type == "MAGIC"))
                    print(item.__dict__)
                    assert isValidItem, "Invalid attack used!"

            isFirstPiece = False

            if item.attackKind == "DO_NOTHING":
                atkData.isAction = True
                attacker.deal += 1
                break
            elif item.attackKind == "DISCARD":
                atkData.isAction = True
                p = list(atkData.piece); p.remove(item)
                for item in p:
                    attacker.discardItem(item.id)
                    for player in self.room.players:
                        if not isinstance(player, Bot):
                            continue
                        if player == attacker:
                            continue
                        player.notify_item_discard(attacker, item.id)
                break
            elif not forced:
                print(atkData.__dict__)
                magicUsed = False
                if item.type == "MAGIC":
                    magicUsed = attacker.magicUsed(item.id, isMagicFree)
                if not magicUsed:
                    if attacker.hasMagic(item.id):
                        assert False, "Failed to use magic " + str(item.id)
                        continue
                    if not attacker.itemUsed(item.id, isMagicFree):
                        assert False, "Failed to use item " + str(item.id)
                        continue
                attacker.deal += 1

            if item.attackKind == "EXCHANGE":
                atkData.isAction = True
                break
            elif item.attackKind == "SELL":
                assert len(atkData.piece) == 2
                print "Sell item:", atkData.piece[1]
                atkData.decidedValue = atkData.piece[1].price
                break

            if item.attackKind == "MYSTERY":
                atkData.isAction = True
                atkData.decidedMystery = "VENUS"  # [MARS,MERCURY,JUPITER,SATURN,URANUS,PLUTO,NEPTUNE,VENUS,EARTH,MOON]

                if atkData.decidedMystery == "VENUS":
                    for p in self.room.players:
                        p.yen = 99
                break

            if item.attackKind == "INCREASE_OR_DECREASE_HP":
                atkData.decidedHP = 10 if random.randrange(0, 2) == 1 else -10
                break

            if item.attackExtra == "INCREASE_ATK":
                attack, _ = item.getAD()

                atkData.damage += attack
                if atkData.attribute is not None and atkData.attribute != item.attribute and item.attribute != "LIGHT":
                    atkData.attribute = ""
            elif item.attackExtra == "DOUBLE_ATK":
                assert len(atkData.piece) > 1, "Tried to use DOUBLE_ATK alone"
                atkData.damage *= 2
                if atkData.attribute is not None and atkData.attribute != item.attribute:
                    atkData.attribute = ""
            elif item.attackExtra == "WIDE_ATK":
                assert len(atkData.piece) > 1, "Tried to use WIDE_ATK alone"
                massiveAttack = True
                atkData.chance = 100
                atkData.attribute = ""
            elif item.attackExtra == "MAGICAL":
                atkData.damage = atkData.attacker.mp * 2
                atkData.attacker.mp = 0
                atkData.extra.append(item.attackExtra)
                break
            else:
                if item.attackExtra and item.attackExtra not in ["ADD_ATTRIBUTE"]:
                    atkData.extra.append(item.attackExtra)
            
            if item.attackKind == "ATK":
                attack, _ = item.getAD()

                if attacker.dead and item.attackExtra == "DYING_ATTACK":
                    attack = atkData.decidedValue

                if item.id == 187:
                    attack = atkData.decidedValue
                if item.id == 190:
                    attack = atkData.decidedValue = atkData.decidedValue * 2

                if item.hitRate > 0 and not massiveAttack:
                    massiveAttack = True
                    atkData.chance = item.hitRate
                    print "Massive attack, chance:", atkData.chance
                
                if not atkData.damage:
                    atkData.damage = attack

                if atkData.attribute is None or item.attackExtra == "ADD_ATTRIBUTE":  # TODO: Maybe ADD_ATTRIBUTE should be processed after all items.
                    atkData.attribute = item.attribute
                elif atkData.attribute != item.attribute and item.attribute != "LIGHT" and item.type != "MAGIC":
                    atkData.attribute = ""
                        
        print "New Attack(M:"+str(massiveAttack)+"):", str(atkData), str(atkData.piece)
            
        if massiveAttack:
            for player in self.room.players:
                if player == attacker:
                    continue
                if player.dead:
                    continue
                if player.team != "SINGLE" and player.team == attacker.team:
                    continue
                _atkData = atkData.copy()
                _atkData.defender = player
                self.attackQueue.put(_atkData)
            _atkData.isLast = True
        else:
            atkData.defender = defender if not atkData.isAction else None
            atkData.isLast = True
            self.attackQueue.put(atkData)

    def doAttack(self, atkData=None):
        if atkData:
            self.currentAttack = atkData
        else:
            atkData = self.currentAttack = self.attackQueue.get()
        missed = False if atkData.defender is not None and "DARK_CLOUD" in atkData.defender.harms else 0 < atkData.chance < random.randrange(0, 100 + 1)

        if not atkData.isAction and atkData.defender.dead:
            if atkData.chance == 0 and (len(atkData.piece) == 0 or atkData.piece[0].defenseKind != "COUNTER"):
                print(str(atkData))
                assert False, "Dead being attacked!"
            return True

        print "Current Attack:", str(atkData)
    
        builder = XMLBuilder("COMMAND")
        #<command><piece><item>1</item><assistantType>VENUS</assistantType></piece><assistantType>VENUS</assistantType><commander><name>Sinbad</name></commander><target><name>Princess Kaguya</name></target></command>
        for item in atkData.piece:
            pp = builder.piece
            pp.item(str(item.id))
            if item.attackExtra == "MAGICAL":
                pp.costMP(str(atkData.damage / 2))
        if missed: builder.isMiss
        if atkData.decidedValue is not None:
            builder.decidedValue(str(atkData.decidedValue))
        if atkData.decidedMystery is not None:
            builder.mystery(atkData.decidedMystery)
            #bResult = builder.mysteryResult
            #for p in self.room.players:
            #    bPlayer = bResult.player
            #    bPlayer.name(p.name)
            #    bPlayer.assistantType("NEPTUNE")
        if atkData.piece[0].id == 2:
            atkData.attacker.hp = 99
            builder.power(key="HP")(str(atkData.attacker.hp))
            atkData.attacker.mp = 99
            builder.power(key="MP")(str(atkData.attacker.mp))
            atkData.attacker.yen = 99
            builder.power(key="YEN")(str(atkData.attacker.yen))
        builder.commander.name(atkData.attacker.name)
        if not atkData.isAction:
            builder.target.name(atkData.defender.name)
        if atkData.decidedHP is not None:
            builder.commandChain.hp(str(atkData.decidedHP))
        if self.server.itemManager.getItem(242) in atkData.piece:
            builder.commandChain.assistantType("VENUS")  # Reset Attack order every 7 ou 5 innings (before send start inning)? or after summom?
        self.room.broadXml(builder)

        if not missed:
            if atkData.isAction:
                return True
            elif atkData.attacker == atkData.defender:
                return self.defenderCommand(atkData.attacker, [])
            elif isinstance(atkData.defender, Bot):
                return self.defenderCommand(atkData.defender, atkData.defender.on_attack())
            return False
        
        return True

    def inflictDamage(self, atkData):
        hasDamaged = atkData.damage > 0

        for item in atkData.piece:
            if item.attackKind == "INCREASE_HP":
                atkData.defender.hp += item.value
            elif item.attackKind == "INCREASE_MP":
                if item.defenseKind == "COUNTER":
                    atkData.attacker.mp += atkData.decidedValue * 2
                else:
                    atkData.defender.mp += item.value
                    if item.isAtkHarm():
                        atkData.defender.addHarm(item.attackExtra)
            elif item.attackKind == "INCREASE_YEN":
                atkData.defender.yen += item.value
            elif item.attackKind == "ABSORB_YEN":
                atkData.attacker.yen += atkData.decidedValue
                atkData.defender.yen -= atkData.decidedValue
                if atkData.defender.yen < 0:
                    atkData.defender.mp -= atkData.defender.yen * -1
                    atkData.defender.yen = 0
                    if atkData.defender.mp < 0:
                        atkData.defender.hp = max(0, atkData.defender.hp - atkData.defender.mp * -1)
                        atkData.defender.mp = 0
            elif item.attackKind == "INCREASE_OR_DECREASE_HP":
                atkData.defender.hp = max(0, atkData.defender.hp + atkData.decidedHP)
            elif item.attackKind == "REMOVE_ALL_HARMS":
                atkData.defender.removeAllHarms()
            elif item.attackKind == "REMOVE_LOWER_HARMS":
                atkData.defender.removeAllHarms(True)
            elif item.attackKind == "ADD_HARM":
                atkData.defender.addHarm(item.attackExtra)
            elif hasDamaged:
                if item.isAtkHarm():
                    atkData.defender.addHarm(item.attackExtra)

        if hasDamaged:
            if atkData.attribute == "DARK":
                atkData.defender.hp = 0
            else:
                if "ABSORB_HP" in atkData.extra:
                    atkData.attacker.hp += atkData.damage
                if "DAMAGE_TO_SELF" in atkData.extra:
                    atkData.attacker.hp = max(0, atkData.attacker.hp - atkData.damage)
                atkData.defender.hp = max(0, atkData.defender.hp - atkData.damage)

    def attackerCommand(self, player, piece, target):
        #if not player == self.attacker:
        #    print "Tentando atacar sem ser attacker"
        #    return

        print "New Attacker Command!"
        print "Used:", str(piece)
        
        self.newAttack(player, target, piece)
        return True

    def defenderCommand(self, player, piece):
        # TODO: Divide defense handing in different classes, like CommandChain, DefenseCommand, Attribute and etc...
        #<COMMAND><piece><item>88</item></piece><commander><name>Igoor</name></commander><target><name>Odin</name></target></COMMAND>""" + chr(0))
        #if not player == self.defender:
        #    print "Tentando defender sem ser defender"
        #    return

        atkData = self.currentAttack.copy()

        blocked = False
        reflected = False
        flicked = False

        isMagicFree = False if len(piece) == 0 else piece[-1].attackExtra == "MAGIC_FREE"
        defenseAttr = None

        #Item 227 e aql martelo, e 50% de chance de acertar mas acerta com 100% quem tem o dangerous mortar

        print "New Defender Command!"
        print "Used:", str(piece)

        for item in piece:
            magicUsed = False
            if item.type == "MAGIC":
                magicUsed = player.magicUsed(item.id, isMagicFree)
            if not magicUsed:
                if player.hasMagic(item.id):
                    assert False, "Failed to use magic " + str(item.id)
                    continue
                if not player.itemUsed(item.id, isMagicFree):
                    assert False, "Failed to use item " + str(item.id)
                    continue
            player.deal += 1

            if item.id == 195:  # REMOVE_ATTRIBUTE
                atkData.attribute = ""
            
            if defenseAttr is None:
                defenseAttr = item.attribute
            elif defenseAttr != item.attribute and item.attribute != "LIGHT":
                defenseAttr = ""

            if (item.defenseExtra == "REFLECT_WEAPON" and atkData.piece[0].type == "WEAPON") or\
               (item.defenseExtra == "REFLECT_MAGIC" and atkData.piece[0].type == "MAGIC") or\
                item.defenseExtra == "REFLECT_ANY":
                reflected = True
                self.currentAttack.attacker, self.currentAttack.defender = self.currentAttack.defender, self.currentAttack.attacker
                self.currentAttack.isRetargeted = True
                atkData = self.currentAttack.copy()
                break
            elif (item.defenseExtra == "FLICK_WEAPON" and atkData.piece[0].type == "WEAPON") or\
                 (item.defenseExtra == "FLICK_MAGIC" and atkData.piece[0].type == "MAGIC"):
                flicked = True
                self.currentAttack.attacker = self.currentAttack.defender
                self.currentAttack.defender = random.choice([player for player in self.room.players if not player.dead])
                self.currentAttack.isRetargeted = True
                atkData = self.currentAttack.copy()
                break
            elif (item.defenseExtra == "BLOCK_WEAPON" and atkData.piece[0].type == "WEAPON") or\
                 (item.defenseExtra == "BLOCK_MAGIC" and atkData.piece[0].type == "MAGIC"):
                blocked = True
                break
            if item.defenseKind == "DFS":
                if item.isDefHarm():
                    atkData.defender.addHarm(item.defenseExtra)
                    
                _, defense = item.getAD()
                
                if False:#item.hitRate > 0:
                    missed = True
                    break
                else:
                    atkData.damage = max(0, atkData.damage - defense)
        
        if not reflected and not flicked and not blocked:
            # Check if that attack could really be defended
            if len(piece) > 0:
                print atkData.attribute, defenseAttr
                assert self.canDefendAttr(atkData.attribute, defenseAttr), "Invalid defense used!"

            if atkData.damage > 0:
                for item in piece:
                    if item.defenseKind == "COUNTER":
                        attacker = atkData.defender
                        defender = atkData.attacker if item.attackKind != "INCREASE_MP" else atkData.defender
                        self.newAttack(attacker, defender, [item], atkData.damage if item.id in [187, 190, 193, 194] else None, True, True)
                    
            self.inflictDamage(atkData)
            if atkData.attacker == atkData.defender:
                print "Self attack, no defense!"
                return True
            
        builder = XMLBuilder("COMMAND")

        noResponse = False
        if not reflected:
            for item in atkData.piece:
                if item.attackKind == "REMOVE_ITEMS":  # Sweep away 1 item
                    itemId = atkData.defender.getRandomItem()
                    if itemId != 0:
                        atkData.defender.discardItem(itemId)
                        builder.commandChain.piece.item(str(itemId))
                        noResponse = True
                        for player in self.room.players:
                            if not isinstance(player, Bot):
                                continue
                            if player == atkData.defender or player == atkData.attacker:
                                continue
                            player.notify_item_discard(atkData.defender, itemId)
                elif item.attackKind == "REMOVE_ABILITIES": # Forget 1 miracle
                    itemId = atkData.defender.getRandomMagic()
                    if itemId != 0:
                        atkData.defender.discardMagic(itemId)
                        builder.commandChain.piece.item(str(itemId))
                        noResponse = True
                        for player in self.room.players:
                            if not isinstance(player, Bot):
                                continue
                            if player == atkData.defender or player == atkData.attacker:
                                continue
                            player.notify_magic_discard(atkData.defender, itemId)
                elif item.attackKind == "BUY":
                    self.buyOportunity = self.server.itemManager.getItem(atkData.defender.getRandomItem())
                    builder.commandChain.piece.item(str(self.buyOportunity.id))
                    noResponse = True

        for player in self.room.players:
            if not isinstance(player, Bot):
                continue
            if player == atkData.defender or player == atkData.attacker:
                continue
            player.notify_attack(atkData, piece, reflected or blocked or flicked)
                
        if not noResponse:
            for item in piece:
                builder.piece.item(str(item.id))

        if reflected or flicked:
            builder.target.name(str(atkData.defender.name))
                        
        # if atkData.attacker.dead and "DYING_ATTACK" in atkData.extra:
        if atkData.decidedValue is not None:
            builder.decidedValue(str(atkData.decidedValue))
            
        self.room.broadXml(builder)

        if reflected or blocked or flicked:
            if blocked:
                return True
            elif atkData.defender.dead:
                return True
            elif atkData.attacker == atkData.defender:
                self.inflictDamage(atkData)
                return True
            elif isinstance(atkData.defender, Bot):
                return self.defenderCommand(atkData.defender, atkData.defender.on_attack())
            return False

        if len(atkData.piece) == 2 and atkData.piece[0].id == 3:
            self.forceItemBuy(atkData.attacker, player, atkData.piece[1])
            return True

        if atkData.piece[0].id == 4:
            if atkData.attacker.yen < self.buyOportunity.price:
                return True

        if self.buyOportunity is None:
            return True
        elif isinstance(atkData.attacker, Bot):
            if atkData.attacker.yen >= self.buyOportunity.price:
                self.playerBuyResponse(atkData.attacker, True)
            return True
        return False
