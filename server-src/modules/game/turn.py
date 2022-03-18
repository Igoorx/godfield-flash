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

        self.abilityIndex = None

        self.decidedValue = None
        self.decidedHP = None
        self.decidedMystery = None
        self.decidedExchange = dict()
        self.decidedItem = None
        self.decidedAssistant = None

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

        copy.abilityIndex = self.abilityIndex

        copy.decidedValue = self.decidedValue
        copy.decidedHP = self.decidedHP
        copy.decidedMystery = self.decidedMystery
        copy.decidedExchange = self.decidedExchange
        copy.decidedItem = self.decidedItem
        copy.decidedAssistant = self.decidedAssistant
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
        assert(atkData.piece[0].attackKind == "BUY")
        assert(atkData.decidedItem is not None)
        assert(atkData.defender.hasItem(atkData.decidedItem.id))
        assert(player == atkData.attacker)

        print "Buy response: ", atkData.decidedItem, player, response
        
        builder = XMLBuilder("BUY")
        
        if response and atkData.attacker.yen >= atkData.decidedItem.price:
            builder.doBuy
            atkData.defender.discardItem(atkData.decidedItem.id)
            atkData.defender.yen += atkData.decidedItem.price
            atkData.attacker.dealItem(atkData.decidedItem.id, True)
            atkData.attacker.yen -= atkData.decidedItem.price
            
        self.room.broadXml(builder)

    def doSell(self):
        atkData = self.currentAttack
        seller, target, piece = atkData.attacker, atkData.defender, atkData.piece[1]
        
        assert(atkData.piece[0].attackKind == "SELL")
        assert(seller.hasItem(piece.id))

        print "Force buy: ", piece, seller, target
        
        seller.discardItem(piece.id)
        seller.yen += piece.price
        print seller.items
        
        target.dealItem(piece.id, True)
        target.yen -= piece.price
        if target.yen < 0:
            target.mp -= target.yen * -1
            target.yen = 0
            if target.mp < 0:
                target.hp = max(0, target.hp - target.mp * -1)
                target.mp = 0
        print target.items

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

    def newAttack(self, attacker, defender, piece, decidedValue=None, decidedExchange=None, forced=False, counter=False):
        # TODO: Maybe divide attack handing in different classes, like CommandChain, AttackCommand, Attribute and etc...

        atkData = AttackData()
        atkData.attacker = attacker
        atkData.piece = piece
        atkData.decidedValue = decidedValue
        atkData.decidedExchange = decidedExchange
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
                                        (item.attackExtra == "MAGIC_FREE" and atkData.piece[0].type == "MAGIC")) # why were we using -1 index?
                    print(item.__dict__)
                    assert isValidItem, "Invalid attack used!"

            isFirstPiece = False

            if item.attackKind == "DO_NOTHING":
                assert len(atkData.piece) == 1
                atkData.isAction = True
                attacker.deal += 1
                break
            elif item.attackKind == "DISCARD":
                atkData.isAction = True
                break
            elif not forced:
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
                assert len(atkData.piece) == 1
                atkData.isAction = True

                sum1 = decidedExchange["HP"] + decidedExchange["MP"] + decidedExchange["YEN"]
                sum2 = attacker.hp + attacker.mp + attacker.yen
                assert(sum1 == sum2)
                break
            elif item.attackKind == "SELL":
                assert len(atkData.piece) == 2
                atkData.decidedValue = atkData.piece[1].price
                break
            elif item.attackKind == "BUY":
                assert len(atkData.piece) == 1
                randomItem = self.server.itemManager.getItem(defender.getRandomItem())
                atkData.decidedItem = randomItem if randomItem.id != 0 else None
                break
            elif item.attackKind == "REMOVE_ITEMS":  # Sweep away 1 item
                assert len(atkData.piece) == 1
                randomItem = self.server.itemManager.getItem(defender.getRandomItem())
                atkData.decidedItem = randomItem if randomItem.id != 0 else None
                break
            elif item.attackKind == "REMOVE_ABILITIES": # Forget 1 miracle
                assert len(atkData.piece) == 1
                randomItem = self.server.itemManager.getItem(defender.getRandomMagic())
                atkData.decidedItem = randomItem if randomItem.id != 0 else None
                if atkData.decidedItem is not None:
                    atkData.abilityIndex = defender.magics.index(randomItem.id)
                break

            if item.attackKind == "MYSTERY":
                atkData.isAction = True
                atkData.decidedMystery = "VENUS"  # [MARS,MERCURY,JUPITER,SATURN,URANUS,PLUTO,NEPTUNE,VENUS,EARTH,MOON]

                if atkData.decidedMystery == "VENUS":
                    for p in self.room.players:
                        p.yen = 99
                break
            elif item.attackKind == "SET_ASSISTANT":
                atkData.decidedAssistant = "VENUS" # [MARS,MERCURY,JUPITER,SATURN,URANUS,PLUTO,NEPTUNE,VENUS,EARTH,MOON]
                break
            elif item.attackKind == "INCREASE_OR_DECREASE_HP":
                atkData.decidedHP = 10 if random.randrange(0, 2) == 1 else -10
                break

            if item.attackExtra == "INCREASE_ATK":
                atkData.damage += item.getAtk()
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
                attack = item.getAtk()

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
        if atkData.piece[0].attackKind == "EXCHANGE":
            builder.power(key="HP")(str(atkData.decidedExchange["HP"]))
            builder.power(key="MP")(str(atkData.decidedExchange["MP"]))
            builder.power(key="YEN")(str(atkData.decidedExchange["YEN"]))
        builder.commander.name(atkData.attacker.name)
        if not atkData.isAction:
            builder.target.name(atkData.defender.name)
        if atkData.decidedHP is not None:
            builder.commandChain.hp(str(atkData.decidedHP))
        if atkData.decidedAssistant is not None:
            builder.commandChain.assistantType(atkData.decidedAssistant) # Reset Attack order every 7 ou 5 innings (before send start inning)? or after summom?
        if atkData.attacker == atkData.defender and atkData.decidedItem is not None:
            pp = builder.commandChain.piece
            pp.item(str(atkData.decidedItem.id))
            if atkData.abilityIndex is not None:
                pp.abilityIndex(str(atkData.abilityIndex))
        self.room.broadXml(builder)

        if not missed:
            if atkData.attacker == atkData.defender or atkData.defender == None:
                return self.defenderCommand(atkData.defender, [])
            elif isinstance(atkData.defender, Bot):
                return self.defenderCommand(atkData.defender, atkData.defender.on_attack())
            return False
        
        print "Attack missed!"
        return True

    def inflictDamage(self, atkData):
        hasDamaged = atkData.damage > 0
        chain = False
        print "InflictDamage: ", str(atkData)

        for item in atkData.piece:
            if item.attackKind == "DISCARD":
                assert(atkData.defender == None)
                p = list(atkData.piece); p.remove(item)
                for item in p:
                    atkData.attacker.discardItem(item.id)
                    for player in self.room.players:
                        if not isinstance(player, Bot):
                            continue
                        if player == atkData.attacker:
                            continue
                        player.notify_item_discard(atkData.attacker, item.id)
                break
            elif item.attackKind == "EXCHANGE":
                assert(atkData.defender == None)
                atkData.attacker.hp = atkData.decidedExchange["HP"]
                atkData.attacker.mp = atkData.decidedExchange["MP"]
                atkData.attacker.yen = atkData.decidedExchange["YEN"]
                break
            elif item.attackKind == "SELL":
                break
            
            elif item.attackKind == "BUY":
                chain = True
                break
            elif item.attackKind == "REMOVE_ITEMS":  # Sweep away 1 item
                chain = True
                if atkData.decidedItem is not None:
                    itemId = atkData.decidedItem.id
                    atkData.defender.discardItem(itemId)
                    for player in self.room.players:
                        if not isinstance(player, Bot):
                            continue
                        if player == atkData.defender or player == atkData.attacker:
                            continue
                        player.notify_item_discard(atkData.defender, itemId)
                break
            elif item.attackKind == "REMOVE_ABILITIES": # Forget 1 miracle
                chain = True
                if atkData.decidedItem is not None:
                    itemId = atkData.decidedItem.id
                    atkData.defender.discardMagic(itemId)
                    for player in self.room.players:
                        if not isinstance(player, Bot):
                            continue
                        if player == atkData.defender or player == atkData.attacker:
                            continue
                        player.notify_magic_discard(atkData.defender, itemId)
                break
            
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

        return chain

    def retargetCurrentAttack(self, attacker, defender):
        atkData = self.currentAttack

        print "Current Attack Retargeted!"
        print atkData.attacker, ">", attacker
        print atkData.defender, ">", defender

        atkData.attacker = attacker
        atkData.defender = defender
        atkData.isRetargeted = True
        
        if atkData.piece[0].attackKind == "BUY":
            assert len(atkData.piece) == 1
            randomItem = self.server.itemManager.getItem(atkData.defender.getRandomItem())
            atkData.decidedItem = randomItem if randomItem.id != 0 else None
        elif atkData.piece[0].attackKind == "REMOVE_ITEMS":  # Sweep away 1 item
            assert len(atkData.piece) == 1
            randomItem = self.server.itemManager.getItem(atkData.defender.getRandomItem())
            atkData.decidedItem = randomItem if randomItem.id != 0 else None
        elif atkData.piece[0].attackKind == "REMOVE_ABILITIES": # Forget 1 miracle
            assert len(atkData.piece) == 1
            randomItem = self.server.itemManager.getItem(atkData.defender.getRandomMagic())
            atkData.decidedItem = randomItem if randomItem.id != 0 else None

    def attackerCommand(self, player, piece, target, decidedExchange=None):
        if self.currentAttack is None:
            assert(player == self.attacker)
        else:
            assert(player == self.currentAttack.attacker)

        print "New Attacker Command!"
        print "Used:", str(piece)
        
        self.newAttack(player, target, piece, None, decidedExchange)
        return True

    def defenderCommand(self, player, piece):
        # TODO: Maybe divide defense handing in different classes, like CommandChain, DefenseCommand, Attribute and etc...
        #<COMMAND><piece><item>88</item></piece><commander><name>Igoor</name></commander><target><name>Odin</name></target></COMMAND>""" + chr(0))
        
        atkData = self.currentAttack.copy()
        assert(player == atkData.defender)

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
                self.retargetCurrentAttack(self.currentAttack.defender, self.currentAttack.attacker)
                atkData = self.currentAttack.copy()
                break
            elif (item.defenseExtra == "FLICK_WEAPON" and atkData.piece[0].type == "WEAPON") or\
                 (item.defenseExtra == "FLICK_MAGIC" and atkData.piece[0].type == "MAGIC"):
                flicked = True
                self.retargetCurrentAttack(self.currentAttack.defender, random.choice([player for player in self.room.players if not player.dead]))
                atkData = self.currentAttack.copy()
                break
            elif (item.defenseExtra == "BLOCK_WEAPON" and atkData.piece[0].type == "WEAPON") or\
                 (item.defenseExtra == "BLOCK_MAGIC" and atkData.piece[0].type == "MAGIC"):
                blocked = True
                break
            if item.defenseKind == "DFS":
                if item.isDefHarm():
                    atkData.defender.addHarm(item.defenseExtra)
                    
                defense = item.getDef()
                
                if False:#item.hitRate > 0:
                    missed = True
                    break
                else:
                    atkData.damage = max(0, atkData.damage - defense)
        
        chain = False
        if not reflected and not flicked and not blocked:
            # Check if that attack could really be defended
            if len(piece) > 0:
                print atkData.attribute, defenseAttr
                assert self.canDefendAttr(atkData.attribute, defenseAttr), "Invalid defense used!"

            if atkData.damage > 0:
                for item in piece:
                    if item.defenseKind != "COUNTER":
                        continue
                    print "Counter attack!"
                    attacker = atkData.defender
                    defender = atkData.attacker if item.attackKind != "INCREASE_MP" else atkData.defender
                    self.newAttack(attacker, defender, [item], atkData.damage if item.id in [187, 190, 193, 194] else None, None, True, True)
                    
            chain = self.inflictDamage(atkData)
            if atkData.attacker == atkData.defender or atkData.defender == None:
                print "Self attack, no defense!"
                return True
            
        builder = XMLBuilder("COMMAND")

        for player in self.room.players:
            if not isinstance(player, Bot):
                continue
            if player == atkData.defender or player == atkData.attacker:
                continue
            player.notify_attack(atkData, piece, reflected or blocked or flicked)
        
        if not reflected and atkData.decidedItem is not None:
            pp = builder.commandChain.piece
            pp.item(str(atkData.decidedItem.id))
            if atkData.abilityIndex is not None:
                pp.abilityIndex(str(atkData.abilityIndex))
        elif not chain:
            for item in piece:
                builder.piece.item(str(item.id))

        if reflected or flicked:
            builder.target.name(str(atkData.defender.name))
                        
        # if atkData.attacker.dead and "DYING_ATTACK" in atkData.extra:
        if atkData.decidedValue is not None:
            builder.decidedValue(str(atkData.decidedValue))
            
        self.room.broadXml(builder)

        if reflected or blocked or flicked:
            assert(atkData.defender != None)
            if blocked or atkData.defender.dead:
                return True
            elif atkData.attacker == atkData.defender:
                self.inflictDamage(atkData)
                return True
            elif isinstance(atkData.defender, Bot):
                return self.defenderCommand(atkData.defender, atkData.defender.on_attack())
            return False

        if atkData.piece[0].attackKind == "SELL":
            self.doSell()
            return True
        elif atkData.piece[0].attackKind == "BUY":
            if atkData.decidedItem is None or atkData.attacker.yen < atkData.decidedItem.price:
                return True
            else:
                if isinstance(atkData.attacker, Bot):
                    self.playerBuyResponse(atkData.attacker, True)
                    return True
                return False

        return True
