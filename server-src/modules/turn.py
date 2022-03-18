from __future__ import annotations
from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from server import Server
    from modules.item import Item
    from modules.room import Room
    from modules.player import Player
from helpers.xmlbuilder import XMLBuilder
from modules.attack import AttackData
from modules.bot import Bot

import random
from queue import Queue

__all__ = ("TurnHandler",)


class TurnHandler:
    room: Room
    server: Server
    currentAttack: Optional[AttackData] 
    attackQueue: Queue[AttackData]
    attacker: Player

    __slots__ = tuple(__annotations__)

    def __init__(self, room: Room):
        self.room = room
        self.server = room.server
        self.new()

    def new(self, attacker: Optional[Player] = None):
        self.currentAttack = None
        self.attackQueue = Queue()
        self.attacker = attacker # type: ignore

    def playerDyingAttack(self, player: Player, item: Item):
        builder = XMLBuilder("DYING")
        builder.piece.item(str(item.id))
        self.room.broadXml(builder)

        if item.attackExtra == "REVIVE":
            print("REVIVE")
            player.discardItem(item.id)
            player.increaseHP(item.value)
        else:
            print("DYING ATTACK")
            builder = XMLBuilder("DIE")
            builder.player.name(player.name)
            self.room.broadXml(builder)
            
            newAttack = AttackData(player, player, [item])
            newAttack.decidedValue = 30
            self.queueAttack(newAttack, True)

    def playerBuyResponse(self, player: Player, response: bool):
        assert self.currentAttack is not None

        atkData = self.currentAttack
        assert atkData.piece[0].attackKind == "BUY"
        assert atkData.decidedItem is not None
        assert atkData.defender.hasItem(atkData.decidedItem.id), f"\"{atkData.defender.name}\" doesn't have decided item \"{atkData.decidedItem.id}\""
        assert player == atkData.attacker

        print("Buy response: ", atkData.decidedItem, player, response)
        
        builder = XMLBuilder("BUY")
        
        if response and atkData.attacker.yen >= atkData.decidedItem.price:
            builder.doBuy
            atkData.defender.discardItem(atkData.decidedItem.id)
            atkData.defender.increaseYen(atkData.decidedItem.price)
            atkData.attacker.dealItem(atkData.decidedItem.id, True)
            atkData.attacker.decreaseYen(atkData.decidedItem.price)
            
        self.room.broadXml(builder)

    def doSell(self):
        atkData = self.currentAttack
        assert atkData is not None
        assert atkData.piece[0].attackKind == "SELL"

        seller, target, piece = atkData.attacker, atkData.defender, atkData.piece[1]
        assert seller.hasItem(piece.id)

        print("Force buy: ", piece, seller, target)
        
        seller.discardItem(piece.id)
        seller.increaseYen(piece.price)
        target.dealItem(piece.id, True)
        target.decreaseYen(piece.price)

    def retargetCurrentAttack(self, attacker: Player, defender: Player):
        atkData = self.currentAttack
        assert atkData is not None

        print("Current Attack Retargeted!")
        print(f"{atkData.attacker} > {attacker}")
        print(f"{atkData.defender} > {defender}")
        
        atkData.attacker = attacker
        atkData.defender = defender
        atkData.isRetargeted = True
        
        if atkData.piece[0].attackKind == "BUY":
            assert len(atkData.piece) == 1
            randomItem = self.server.itemManager.getItem(atkData.defender.getRandomItem())
            atkData.decidedItem = randomItem if randomItem.id != 0 else None
            print(f"Decided item for \"{defender.name}\": {atkData.decidedItem}")
        elif atkData.piece[0].attackKind == "REMOVE_ITEMS":  # Sweep away 1 item
            assert len(atkData.piece) == 1
            randomItem = self.server.itemManager.getItem(atkData.defender.getRandomItem())
            atkData.decidedItem = randomItem if randomItem.id != 0 else None
            print(f"Decided item for \"{defender.name}\": {atkData.decidedItem}")
        elif atkData.piece[0].attackKind == "REMOVE_ABILITIES": # Forget 1 miracle
            assert len(atkData.piece) == 1
            randomItem = self.server.itemManager.getItem(atkData.defender.getRandomMagic())
            atkData.decidedItem = randomItem if randomItem.id != 0 else None
            if atkData.decidedItem is not None:
                atkData.abilityIndex = defender.magics.index(randomItem.id)
            print(f"Decided item for \"{defender.name}\": {atkData.decidedItem}")

    def queueAttack(self, atkData: AttackData, forced = False):
        # TODO: Maybe divide attack handing in different classes, like CommandChain, AttackCommand, Attribute and etc...
        assert forced or len(atkData.piece) > 0
        assert forced or not atkData.attacker.dead, f"\"{atkData.attacker.name}\" is dead but tried to attack!"
        assert forced or not atkData.defender.dead, f"\"{atkData.defender.name}\" attacked but is dead!"
        
        if "FOG" in atkData.attacker.harms and atkData.attacker != atkData.defender:
            getRandomAlive = self.room.getRandomAliveEnemy if atkData.attacker.isEnemy(atkData.defender) else self.room.getRandomAliveAlly
            atkData.defender = getRandomAlive(atkData.attacker)
            print(f"Attack target changed to: {atkData.defender}")

        massiveAttack = False
        isMagicFree = False if len(atkData.piece) == 0 else atkData.piece[-1].attackExtra == "MAGIC_FREE"
        isFirstPiece = True
        
        for item in atkData.piece:
            if not forced:
                isValidItem = False
                if isFirstPiece:
                    isValidItem = item.type != "PROTECTOR" and (item.type not in ["MAGIC", "SUNDRY"] or item.attackKind)
                else:
                    isValidItem = item.attackKind not in ["DO_NOTHING", "DISCARD", "SELL", "EXCHANGE", "MYSTERY"] and\
                                    ((item.attackExtra in ["INCREASE_ATK", "DOUBLE_ATK", "WIDE_ATK", "ADD_ATTRIBUTE"] and\
                                      atkData.piece[0].type == "WEAPON" and atkData.piece[0].hitRate == 0) or\
                                        (item.attackExtra == "MAGIC_FREE" and atkData.piece[0].type == "MAGIC")) # why were we using -1 index?
                assert isValidItem, f"Invalid attack used! (Item: {repr(item)})"

            isFirstPiece = False

            if item.attackKind == "DO_NOTHING":
                assert len(atkData.piece) == 1
                atkData.isAction = True
                atkData.attacker.deal += 1
                break
            elif item.attackKind == "DISCARD":
                atkData.isAction = True
                break
            elif not forced:
                usedMagic = False
                if item.type == "MAGIC":
                    usedMagic = atkData.attacker.tryUseMagic(item.id, isMagicFree)
                if not usedMagic:
                    assert not atkData.attacker.hasMagic(item.id), f"\"{atkData.attacker.name}\" failed to use magic {item.id}"
                    atkData.attacker.useItem(item.id, isMagicFree)
                atkData.attacker.deal += 1

            if item.attackKind == "EXCHANGE":
                assert len(atkData.piece) == 1
                assert atkData.decidedExchange is not None
                atkData.isAction = True

                sum1 = atkData.decidedExchange["HP"] + atkData.decidedExchange["MP"] + atkData.decidedExchange["YEN"]
                sum2 = atkData.attacker.hp + atkData.attacker.mp + atkData.attacker.yen
                assert sum1 == sum2
                break
            elif item.attackKind == "SELL":
                assert len(atkData.piece) == 2
                atkData.decidedValue = atkData.piece[1].price
                break
            elif item.attackKind == "BUY":
                assert len(atkData.piece) == 1
                randomItem = self.server.itemManager.getItem(atkData.defender.getRandomItem())
                atkData.decidedItem = randomItem if randomItem.id != 0 else None
                print(f"Decided item for \"{atkData.defender.name}\": {atkData.decidedItem}")
                break
            elif item.attackKind == "REMOVE_ITEMS":  # Sweep away 1 item
                assert len(atkData.piece) == 1
                randomItem = self.server.itemManager.getItem(atkData.defender.getRandomItem())
                atkData.decidedItem = randomItem if randomItem.id != 0 else None
                print(f"Decided item for \"{atkData.defender.name}\": {atkData.decidedItem}")
                break
            elif item.attackKind == "REMOVE_ABILITIES": # Forget 1 miracle
                assert len(atkData.piece) == 1
                randomItem = self.server.itemManager.getItem(atkData.defender.getRandomMagic())
                atkData.decidedItem = randomItem if randomItem.id != 0 else None
                if atkData.decidedItem is not None:
                    atkData.abilityIndex = atkData.defender.magics.index(randomItem.id)
                print(f"Decided item for \"{atkData.defender.name}\": {atkData.decidedItem}")
                break

            if item.attackKind == "MYSTERY":
                assert len(atkData.piece) == 1
                atkData.isAction = True
                atkData.decidedMystery = random.choice(["MARS", "MERCURY", "JUPITER", "SATURN", "URANUS", "PLUTO", "NEPTUNE", "VENUS", "EARTH", "MOON"])
                
                if atkData.decidedMystery == "MARS":
                    for player in self.room.players:
                        player.disease = "FEVER"
                elif atkData.decidedMystery == "MERCURY":
                    for player in self.room.players:
                        player.addHarm("FOG")
                elif atkData.decidedMystery == "JUPITER":
                    for player in self.room.players:
                        player.addHarm("ILLUSION")
                elif atkData.decidedMystery == "SATURN":
                    for player in self.room.players:
                        player.hp = 1
                elif atkData.decidedMystery == "URANUS":
                    atkData.isAction = False
                    atkData.defender = self.room.getRandomAlive()
                    atkData.damage = 60
                    atkData.attribute = "LIGHT"
                elif atkData.decidedMystery == "PLUTO":
                    massiveAttack = True
                    atkData.isAction = False
                    atkData.chance = 75
                    atkData.damage = 30
                    atkData.attribute = "DARK"
                elif atkData.decidedMystery == "NEPTUNE":
                    atkData.attacker.increaseHP(60)
                elif atkData.decidedMystery == "VENUS":
                    for player in self.room.players:
                        player.yen = 99
                elif atkData.decidedMystery == "EARTH":
                    everyoneItemCount: dict[Player, int] = {}
                    everyoneItemList: list[int] = []
                    for player in self.room.players:
                        everyoneItemCount[player] = len(player.items)
                        everyoneItemList += player.items
                        player.items = list()
                    for player, itemCount in everyoneItemCount.items():
                        while len(player.items) < itemCount:
                            itemIdx = random.randrange(0, len(everyoneItemList))
                            player.items.append(everyoneItemList[itemIdx])
                            del everyoneItemList[itemIdx]
                elif atkData.decidedMystery == "MOON":
                    for player in self.room.players:
                        player.assistantType = random.choice(["MARS", "MERCURY", "JUPITER", "SATURN", "URANUS", "PLUTO", "NEPTUNE", "VENUS", "EARTH", "MOON"])
                        player.assistantHP = 20
                break
            elif item.attackKind == "SET_ASSISTANT":
                assert len(atkData.piece) == 1
                atkData.decidedAssistant = random.choice(["MARS", "MERCURY", "JUPITER", "SATURN", "URANUS", "PLUTO", "NEPTUNE", "VENUS", "EARTH", "MOON"])
                break
            elif item.attackKind == "INCREASE_OR_DECREASE_HP":
                assert len(atkData.piece) == 1
                atkData.decidedHP = 10 if random.randrange(0, 2) == 1 else -10
                break
            elif item.attackKind == "ADD_ITEM":
                assert len(atkData.piece) == 1
                atkData.piece.append(self.server.itemManager.getProbRandomItems(1)[0])
                break

            if item.attackExtra == "INCREASE_ATK":
                if atkData.damage == -1:
                    atkData.damage = 0
                atkData.damage += item.getAtk()
            elif item.attackExtra == "DOUBLE_ATK":
                assert atkData.damage >= 0 and len(atkData.piece) > 1, "Tried to use DOUBLE_ATK alone"
                atkData.damage *= 2
            elif item.attackExtra == "WIDE_ATK":
                assert len(atkData.piece) > 1, "Tried to use WIDE_ATK alone"
                massiveAttack = True
                atkData.chance = 100
                atkData.attribute = ""
            elif item.attackExtra == "MAGICAL":
                atkData.damage = atkData.attacker.mp * 2
                atkData.attacker.mp = 0
                atkData.extra.append(item.attackExtra)
            elif item.attackExtra == "PESTLE":
                assert len(atkData.piece) == 1
                mortarOwner = None
                for player in self.room.players:
                    if player.dead:
                        continue
                    if any(item == 245 for item in player.items):
                        mortarOwner = player
                        break
                if mortarOwner is not None:
                    atkData.mortarId = 245
                    atkData.damage = 99
                    atkData.defender = mortarOwner
                else:
                    atkData.defender = self.room.getRandomAlive()
                print("Mortar attack target selected.")
            else:
                if item.attackExtra and item.attackExtra not in ["ADD_ATTRIBUTE"]:
                    atkData.extra.append(item.attackExtra)
            
            if item.attackKind == "ATK":
                attack = item.getAtk()
                
                if atkData.attacker.dead and item.attackExtra == "DYING_ATTACK":
                    assert atkData.decidedValue is not None
                    attack = atkData.decidedValue

                if item.id == 187:
                    assert atkData.decidedValue is not None
                    attack = atkData.decidedValue
                elif item.id == 190:
                    assert atkData.decidedValue is not None
                    attack = atkData.decidedValue = atkData.decidedValue * 2

                if item.hitRate > 0 and not massiveAttack:
                    massiveAttack = True
                    atkData.chance = item.hitRate
                    print(f"Massive attack, chance: {atkData.chance}")
                
                if atkData.damage == -1:
                    atkData.damage = attack

            if atkData.attribute is None or atkData.attribute == "LIGHT" or item.attackExtra == "ADD_ATTRIBUTE":
                atkData.attribute = item.attribute
            elif atkData.attribute != item.attribute and item.attribute != "LIGHT":
                atkData.attribute = ""                
        
        if massiveAttack:
            assert not atkData.isAction and atkData.chance > 0
            print(f"New Massive Attack: {atkData}, {atkData.piece}")
            _atkData = None
            for player in self.room.players:
                if player.dead:
                    continue
                if not player.isEnemy(atkData.attacker):
                    continue
                _atkData = atkData.clone()
                _atkData.defender = player
                self.attackQueue.put(_atkData)
            assert _atkData is not None
            _atkData.isLast = True
        else:
            if atkData.isAction:
                if atkData.defender != atkData.attacker:
                    print(f"Attack target changed to attacker due to it being an action.")
                atkData.defender = atkData.attacker
            elif "TO_ENEMY" in atkData.extra:
                print(f"Attack target changed to random enemy due to attackExtra.")
                atkData.defender = self.room.getRandomAliveEnemy(atkData.attacker)
            print(f"New Attack: {atkData}, {atkData.piece}")
            atkData.isLast = True
            self.attackQueue.put(atkData)

    def doAttack(self, atkData: Optional[AttackData] = None) -> bool:
        if atkData is not None:
            self.currentAttack = atkData
        else:
            atkData = self.currentAttack = self.attackQueue.get()
        missed = False if "DARK_CLOUD" in atkData.defender.harms else 0 < atkData.chance < random.randrange(1, 100 + 1)

        if not atkData.isAction and atkData.defender.dead:
            if atkData.chance == 0 and (len(atkData.piece) == 0 or atkData.piece[0].defenseKind != "COUNTER"):
                print(str(atkData))
                assert False, "Dead being attacked!"
            return True

        print("Current Attack:", str(atkData))
        
        # We need to build the XML for every user because of the MYSTERY "EARTH"...
        # TODO: maybe this could be improved if we could somehow copy the XMLBuilder
        for user in self.room.users:
            builder = XMLBuilder("COMMAND")
            #<command><piece><item>1</item><assistantType>VENUS</assistantType></piece><assistantType>VENUS</assistantType><commander><name>Sinbad</name></commander><target><name>Princess Kaguya</name></target></command>
            for item in atkData.piece:
                bPiece = builder.piece
                bPiece.item(str(item.id))
                if item.attackExtra == "MAGICAL":
                    bPiece.costMP(str(atkData.damage // 2))
                if item.assistantType:
                    bPiece.assistantType(item.assistantType)
            if missed:
                builder.isMiss
            if atkData.decidedValue is not None:
                builder.decidedValue(str(atkData.decidedValue))
            if atkData.mortarId is not None:
                builder.mortar.item(str(atkData.mortarId))
            if atkData.decidedMystery is not None:
                builder.mystery(atkData.decidedMystery)
                if atkData.decidedMystery == "EARTH" and user.player is not None:
                    bResult = builder.mysteryResult
                    for item in user.player.items:
                        bResult.item(str(item))
                elif atkData.decidedMystery == "MOON":
                    bResult = builder.mysteryResult
                    for player in self.room.players:
                        bPlayer = bResult.player
                        bPlayer.name(player.name)
                        bPlayer.assistantType(player.assistantType)
            if atkData.piece[0].attackKind == "EXCHANGE" and atkData.decidedExchange is not None:
                builder.power(key="HP")(str(atkData.decidedExchange["HP"]))
                builder.power(key="MP")(str(atkData.decidedExchange["MP"]))
                builder.power(key="YEN")(str(atkData.decidedExchange["YEN"]))
            if atkData.piece[0].assistantType:
                builder.assistantType(atkData.piece[0].assistantType)
            builder.commander.name(atkData.attacker.name)
            if not atkData.isAction:
                builder.target.name(atkData.defender.name)
            if atkData.decidedHP is not None:
                builder.commandChain.hp(str(atkData.decidedHP))
            if atkData.decidedAssistant is not None:
                builder.commandChain.assistantType(atkData.decidedAssistant) # Reset Attack order every 7 ou 5 innings (before send start inning)? or after summom?
            if atkData.attacker == atkData.defender and atkData.decidedItem is not None:
                bPiece = builder.commandChain.piece
                bPiece.item(str(atkData.decidedItem.id))
                if atkData.abilityIndex is not None:
                    bPiece.abilityIndex(str(atkData.abilityIndex))
            user.sendXml(builder)

        if not missed:
            if atkData.attacker == atkData.defender or atkData.defender.dead:
                return self.defenderCommand(atkData.defender, [])
            elif isinstance(atkData.defender, Bot):
                return self.defenderCommand(atkData.defender, atkData.defender.onDefenseTurn())
            return False
        
        print("Attack missed!")
        return True

    def inflictDamage(self, atkData: AttackData) -> bool:
        hasDamaged = atkData.damage > 0
        chain = False
        print(f"InflictDamage: {atkData}")

        for item in atkData.piece:
            if item.attackKind == "DISCARD":
                assert atkData.attacker == atkData.defender
                piece = [i for i in atkData.piece if i != item]
                for item in piece:
                    atkData.attacker.discardItem(item.id)
                    for player in self.room.players:
                        if not isinstance(player, Bot):
                            continue
                        if player == atkData.attacker:
                            continue
                        player.notify_item_discard(atkData.attacker, item.id)
                break
            elif item.attackKind == "EXCHANGE":
                assert atkData.attacker == atkData.defender
                assert atkData.decidedExchange is not None
                atkData.attacker.hp = atkData.decidedExchange["HP"]
                atkData.attacker.mp = atkData.decidedExchange["MP"]
                atkData.attacker.yen = atkData.decidedExchange["YEN"]
                break
            elif item.attackKind == "SELL":
                break
            elif item.attackKind == "ADD_ITEM":
                assert len(atkData.piece) == 2
                atkData.defender.dealItem(atkData.piece[1].id, True)
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
                        if player in [atkData.defender, atkData.attacker]:
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
                        if player in [atkData.defender, atkData.attacker]:
                            continue
                        player.notify_magic_discard(atkData.defender, itemId)
                break

            if item.attackKind == "INCREASE_HP":
                atkData.defender.increaseHP(item.value)
            elif item.attackKind == "INCREASE_MP":
                if item.defenseKind == "COUNTER":
                    assert atkData.decidedValue is not None
                    atkData.attacker.increaseMP(atkData.decidedValue * 2)
                else:
                    atkData.defender.increaseMP(item.value)
                if item.isAtkHarm():
                    atkData.defender.addHarm(item.attackExtra)
            elif item.attackKind == "INCREASE_YEN":
                atkData.defender.increaseYen(item.value)
            elif item.attackKind == "ABSORB_YEN":
                if atkData.decidedValue is not None:
                    atkData.attacker.increaseYen(atkData.decidedValue)
                    atkData.defender.decreaseYen(atkData.decidedValue)
                else:
                    atkData.attacker.increaseYen(item.value)
                    atkData.defender.decreaseYen(item.value)
            elif item.attackKind == "SCATTER_YEN":
                for player in self.room.players:
                    player.increaseYen(item.value)
            elif item.attackKind == "SET_ASSISTANT":
                assert atkData.decidedAssistant is not None
                atkData.defender.assistantType = atkData.decidedAssistant
                atkData.defender.assistantHP = 20
            elif item.attackKind == "INCREASE_OR_DECREASE_HP":
                assert atkData.decidedHP is not None
                if atkData.decidedHP < 0:
                    atkData.defender.takeDamage(atkData.decidedHP * -1)
                else:
                    atkData.defender.increaseHP(atkData.decidedHP)
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
                atkData.defender.assistantType = ""
                atkData.defender.assistantHP = 0
            else:
                if "ABSORB_HP" in atkData.extra:
                    atkData.attacker.increaseHP(atkData.damage)
                if "DAMAGE_TO_SELF" in atkData.extra:
                    atkData.attacker.takeDamage(atkData.damage)
                atkData.defender.takeDamage(atkData.damage)

        return chain

    def attackerCommand(self, player: Player, piece: list[Item], target: Player, decidedExchange: Optional[dict[str, int]] = None) -> bool:
        if self.currentAttack is None:
            assert player == self.attacker
        else:
            assert player == self.currentAttack.attacker

        print("New Attacker Command!")
        print(f"Used: {piece}")

        newAttack = AttackData(player, target, piece)
        newAttack.decidedExchange = decidedExchange
        self.queueAttack(newAttack)
        return True

    def defenderCommand(self, player: Player, piece: list[Item]) -> bool:
        # TODO: Maybe divide defense handing in different classes, like CommandChain, DefenseCommand, Attribute and etc...
        #<COMMAND><piece><item>88</item></piece><commander><name>Igoor</name></commander><target><name>Odin</name></target></COMMAND>""" + chr(0))
        
        assert self.currentAttack is not None
        atkData = self.currentAttack.clone()
        assert player == atkData.defender

        blocked = False
        reflected = False
        flicked = False

        isMagicFree = False if len(piece) == 0 else piece[-1].attackExtra == "MAGIC_FREE"
        defenseAttr = None

        #Item 227 e aql martelo, e 50% de chance de acertar mas acerta com 100% quem tem o dangerous mortar

        print("New Defender Command!")
        print("Used:", str(piece))

        for item in piece:
            magicUsed = False
            if item.type == "MAGIC":
                magicUsed = player.tryUseMagic(item.id, isMagicFree)
            if not magicUsed:
                assert not player.hasMagic(item.id), f"\"{player.name}\" failed to use magic {item.id}"
                player.useItem(item.id, isMagicFree)
            player.deal += 1

            if item.id == 195:  # REMOVE_ATTRIBUTE
                atkData.attribute = ""
            
            if defenseAttr is None or defenseAttr == "LIGHT":
                defenseAttr = item.attribute
            elif defenseAttr != item.attribute and item.attribute != "LIGHT":
                defenseAttr = ""

            if (item.defenseExtra == "REFLECT_WEAPON" and atkData.piece[0].type == "WEAPON") or\
               (item.defenseExtra == "REFLECT_MAGIC" and atkData.piece[0].type == "MAGIC") or\
                item.defenseExtra == "REFLECT_ANY":
                reflected = True
                self.retargetCurrentAttack(self.currentAttack.defender, self.currentAttack.attacker)
                atkData = self.currentAttack.clone()
                break
            elif (item.defenseExtra == "FLICK_WEAPON" and atkData.piece[0].type == "WEAPON") or\
                 (item.defenseExtra == "FLICK_MAGIC" and atkData.piece[0].type == "MAGIC"):
                flicked = True
                self.retargetCurrentAttack(self.currentAttack.defender, self.room.getRandomAlive())
                atkData = self.currentAttack.clone()
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
                print(atkData.attribute, defenseAttr)
                assert atkData.canBeDefendedBy(defenseAttr), "Invalid defense used!"

            if atkData.damage > 0:
                for item in piece:
                    if item.defenseKind != "COUNTER":
                        continue
                    print("Counter attack!")
                    target = atkData.attacker if item.attackKind != "INCREASE_MP" else atkData.defender
                    newAttack = AttackData(atkData.defender, target, [item])
                    newAttack.decidedValue = atkData.damage if item.id in [187, 190, 193, 194] else None
                    newAttack.isCounter = True
                    self.queueAttack(newAttack, True)
                    
            chain = self.inflictDamage(atkData)
            if atkData.attacker == atkData.defender:
                print("Self attack, no defense!")
                return True
            if atkData.mortarId is not None:
                print("Mortar attack, no defense!")
                return True
            
        builder = XMLBuilder("COMMAND")

        for player in self.room.players:
            if not isinstance(player, Bot):
                continue
            if player in [atkData.defender, atkData.attacker]:
                continue
            player.notify_attack(atkData, piece, reflected or blocked or flicked)
        
        if not reflected and atkData.decidedItem is not None:
            bPiece = builder.commandChain.piece
            bPiece.item(str(atkData.decidedItem.id))
            if atkData.abilityIndex is not None:
                bPiece.abilityIndex(str(atkData.abilityIndex))
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
            if blocked or atkData.defender.dead:
                return True
            elif atkData.attacker == atkData.defender:
                self.inflictDamage(atkData)
                return True
            elif isinstance(atkData.defender, Bot):
                return self.defenderCommand(atkData.defender, atkData.defender.onDefenseTurn())
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
