from __future__ import annotations
from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from server import Server
    from modules.room import Room
    from modules.player import Player
from helpers.xmlbuilder import XMLBuilder
from modules.item import Item
from modules.commandPiece import CommandPiece
from modules.attackData import AttackData
from modules.assistant import Assistant

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

    def playerDyingAttack(self, player: Player, piece: CommandPiece):
        builder = XMLBuilder("DYING")
        piece.writeXML(builder.piece)
        self.room.broadXml(builder)

        if piece.item.attackExtra == "REVIVE":
            print("REVIVE")
            player.discardPiece(piece)
            player.increaseHP(piece.item.value)
        else:
            print("DYING ATTACK")
            newAttack = AttackData(player, player, [piece])
            piece.illusionItem = None
            newAttack.decidedValue = 30
            self.queueAttack(newAttack, True)

    def playerBuyResponse(self, player: Player, response: bool):
        assert self.currentAttack is not None

        atkData = self.currentAttack
        assert player == atkData.attacker
        assert atkData.pieceList[0].item.attackKind == "BUY"
        assert atkData.decidedPiece is not None

        decidedItem = atkData.decidedPiece.item
        assert atkData.defender.hasOwnedPiece(atkData.decidedPiece), f"\"{atkData.defender.name}\" doesn't have decided item \"{decidedItem.id}\""

        print("Buy response: ", decidedItem, player, response)

        builder = XMLBuilder("BUY")

        if response and atkData.attacker.yen >= decidedItem.price:
            builder.doBuy
            atkData.defender.discardPiece(atkData.decidedPiece)
            atkData.defender.increaseYen(decidedItem.price)
            atkData.attacker.dealItem(decidedItem.id, True)
            atkData.attacker.decreaseYen(decidedItem.price)

        self.room.broadXml(builder)

    def convertPiecesToOwnedPieces(self, player: Player, pieceList: list[CommandPiece]):
        for idx in range(len(pieceList)):
            piece = pieceList[idx]
            if piece.item.type == "FIXED" or piece.isAbility:
                continue
            ownedPiece = player.getOwnedPiece(piece, pieceList)
            if ownedPiece is None:
                print(idx)
                print(pieceList)
                print([str(id(p)) for p in pieceList])
                print(player.pieces)
                print([str(id(p)) for p in player.pieces])
                assert False, f"\"{player.name}\" tried to use a item he doesn't have!"
            pieceList[idx] = ownedPiece

    def queueAttack(self, atkData: AttackData, forced = False):
        # TODO: Maybe divide attack handing in different classes, like CommandChain, AttackCommand, Attribute and etc...
        assert forced or len(atkData.pieceList) > 0
        assert forced or not atkData.attacker.dead, f"\"{atkData.attacker.name}\" is dead but tried to attack!"
        assert forced or not atkData.defender.dead, f"\"{atkData.defender.name}\" attacked but is dead!"

        print(f"QueueAttack: pieceList={atkData.pieceList}")

        if not forced and "FOG" in atkData.attacker.harms and atkData.attacker != atkData.defender:
            getRandomAlive = self.room.getRandomAliveEnemy if atkData.attacker.isEnemy(atkData.defender) else self.room.getRandomAliveAlly
            atkData.defender = getRandomAlive(atkData.attacker)
            print(f"Attack target changed to: {atkData.defender}")

        magicFreeIdxList: list[int] = []
        for idx, piece in enumerate(atkData.pieceList):
            if idx > 0 and piece.item.attackExtra == "MAGIC_FREE":
                assert idx - 1 not in magicFreeIdxList
                magicFreeIdxList.append(idx - 1)
                break

        massiveAttack = False
        usedMagic = False
        magicalPiece: Optional[CommandPiece] = None

        if not forced:
            self.convertPiecesToOwnedPieces(atkData.attacker, atkData.pieceList)
            print(f"ownedPieceList={atkData.pieceList}")

        for idx, piece in enumerate(atkData.pieceList):
            item = piece.item
            if not forced:
                assert atkData.isValidAttackItem(item, idx == 0, usedMagic), f"Invalid attack used! (Item: {repr(item)})"

            isMagicFree = idx in magicFreeIdxList

            if item.attackKind == "DO_NOTHING":
                assert len(atkData.pieceList) == 1
                assert not any(item.type == "WEAPON" for item in atkData.attacker.getItems())
                atkData.isAction = True
                atkData.attacker.deal += 1
                break
            elif item.attackKind == "DISCARD":
                assert len(atkData.pieceList) > 1
                atkData.isAction = True
                break
            elif not forced:
                if piece.isAbility:
                    atkData.attacker.useMagic(item.id, isMagicFree)
                else:
                    atkData.attacker.usePiece(piece, isMagicFree)
                atkData.attacker.deal += 1

            if item.type == "MAGIC":
                usedMagic = True
                if magicalPiece is not None and not isMagicFree:
                    magicalPiece.costMP = atkData.attacker.mp
                    atkData.damage = atkData.attacker.mp * 2

            if usedMagic and item.attackExtra == "MAGIC_FREE":
                continue

            if item.attackKind == "EXCHANGE":
                assert len(atkData.pieceList) == 1
                assert atkData.decidedExchange is not None
                atkData.isAction = True

                sum1 = atkData.decidedExchange["HP"] + atkData.decidedExchange["MP"] + atkData.decidedExchange["YEN"]
                sum2 = atkData.attacker.hp + atkData.attacker.mp + atkData.attacker.yen
                assert sum1 == sum2, str(atkData.decidedExchange)
                break
            elif item.attackKind == "SELL":
                assert len(atkData.pieceList) == 2
                if atkData.assistantType is None:
                    atkData.attacker.discardPiece(atkData.pieceList[1])
                atkData.decidedValue = atkData.pieceList[1].item.price
                break
            elif item.attackKind == "BUY":
                assert len(atkData.pieceList) == 1
                break
            elif item.attackKind == "REMOVE_ITEMS":  # Sweep away 1 item
                assert len(atkData.pieceList) == 1
                break
            elif item.attackKind == "REMOVE_ABILITIES": # Forget 1 miracle
                assert len(atkData.pieceList) == 1
                break

            if item.attackKind == "MYSTERY":
                assert len(atkData.pieceList) == 1
                atkData.isAction = True
                atkData.decidedMystery = random.choice(Assistant.VALID_TYPES)

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
                    everyoneItemList: list[Item] = []
                    for player in self.room.players:
                        everyoneItemCount[player] = len(player.pieces)
                        everyoneItemList += list(player.getItems())
                        player.pieces = list()
                    for player, itemCount in everyoneItemCount.items():
                        while len(player.pieces) < itemCount:
                            itemIdx = random.randrange(0, len(everyoneItemList))
                            player.pieces.append(CommandPiece(everyoneItemList[itemIdx]))
                            del everyoneItemList[itemIdx]
                elif atkData.decidedMystery == "MOON":
                    for player in self.room.players:
                        player.assistant = Assistant.createRandom(player)
                break
            elif item.attackKind == "SET_ASSISTANT":
                assert len(atkData.pieceList) == 1 + (1 if isMagicFree else 0)
                if self.room.forceNextAssistant is not None:
                    atkData.decidedAssistant = self.room.forceNextAssistant
                    self.room.forceNextAssistant = None
                else:
                    atkData.decidedAssistant = random.choice(Assistant.VALID_TYPES)
                break
            elif item.attackKind == "INCREASE_OR_DECREASE_HP":
                assert len(atkData.pieceList) == 1
                atkData.decidedHP = 10 if random.randrange(0, 2) == 1 else -10
                break
            elif item.attackKind == "ADD_ITEM":
                assert len(atkData.pieceList) == 2
                break

            if item.attackExtra == "INCREASE_ATK":
                if atkData.damage == -1:
                    atkData.damage = 0
                atkData.damage += item.getAtk()
            elif item.attackExtra == "DOUBLE_ATK":
                assert atkData.damage >= 0 and len(atkData.pieceList) > 1, "Tried to use DOUBLE_ATK alone"
                atkData.damage *= 2
            elif item.attackExtra == "WIDE_ATK":
                assert atkData.damage >= 0 and len(atkData.pieceList) > 1, "Tried to use WIDE_ATK alone"
                massiveAttack = True
                atkData.chance = 100
                atkData.attribute = ""
            elif item.attackExtra == "MAGICAL":
                if atkData.assistantType is None:
                    magicalPiece = piece
                    magicalPiece.costMP = atkData.attacker.mp
                    atkData.damage = atkData.attacker.mp * 2
                else:
                    piece.costMP = 100
                    atkData.damage = 200
                atkData.extra.append(item.attackExtra)
            elif item.attackExtra == "PESTLE":
                assert len(atkData.pieceList) == 1
                mortar = None
                for player in self.room.players:
                    if player.dead:
                        continue
                    mortarPiece = player.getOwnedPieceById(245)
                    if mortarPiece is not None:
                        mortar = (player, mortarPiece)
                        break
                if mortar is not None:
                    atkData.mortar = mortar[1]
                    atkData.damage = 999
                    atkData.defender = mortar[0]
                else:
                    atkData.defender = self.room.getRandomAlive()
                print("Mortar attack target selected.")
            else:
                if item.attackExtra and item.attackExtra not in ["ADD_ATTRIBUTE"]:
                    atkData.extra.append(item.attackExtra)

            if item.attackKind == "ATK":
                attack = item.getAtk()

                if atkData.decidedValue is not None:
                    assert item.attackExtra == "DYING_ATTACK" or atkData.isCounter
                    attack = atkData.decidedValue

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

        if magicalPiece is not None:
            atkData.attacker.mp = 0

        if massiveAttack:
            assert not atkData.isAction and atkData.chance > 0
            print(f"New Massive Attack: {atkData}, {atkData.pieceList}")
            _atkData = None
            for player in self.room.players:
                if player.dead:
                    continue
                if not player.isEnemy(atkData.attacker):
                    continue
                _atkData = atkData.clone()
                _atkData.defender = player
                self.attackQueue.put(_atkData)
            if _atkData is None:
                print("No alive enemy was found, massive attack wasn't executed.")
                return
            _atkData.isLast = True
        else:
            if atkData.isAction:
                if atkData.defender != atkData.attacker:
                    print("Attack target changed to attacker due to it being an action.")
                atkData.defender = atkData.attacker
            elif "TO_ENEMY" in atkData.extra and self.room.areEnemiesAlive(atkData.attacker):
                print("Attack target changed to random enemy due to attackExtra.")
                atkData.defender = self.room.getRandomAliveEnemy(atkData.attacker)
            print(f"New Attack: {atkData}, {atkData.pieceList}")
            atkData.isLast = True
            self.attackQueue.put(atkData)

    def doAttack(self, atkData: Optional[AttackData] = None) -> bool:
        if atkData is not None:
            self.currentAttack = atkData
        else:
            atkData = self.currentAttack = self.attackQueue.get()
        missed = False if "DARK_CLOUD" in atkData.defender.harms else 0 < atkData.chance < random.randrange(1, 100 + 1)

        if atkData.defender.dead:
            assert atkData.chance != 0 or atkData.isCounter or atkData.assistantType, f"Dead being attacked! ({atkData}, Piece={atkData.pieceList})"
            print("Attack skipped because defender is dead.")
            return True

        print(f"Current Attack: {atkData}")

        endInning = missed
        if atkData.attacker == atkData.defender:
            endInning = self.defenderCommand(atkData.defender, [])

        # We need to build the XML for every user because of the MYSTERY "EARTH"...
        # TODO: maybe this could be improved if we could somehow copy the XMLBuilder
        for user in self.room.users:
            builder = XMLBuilder("COMMAND")
            for piece in atkData.pieceList:
                piece.writeXML(builder.piece)
            if missed:
                builder.isMiss
            if atkData.decidedValue is not None:
                builder.decidedValue(str(atkData.decidedValue))
            if atkData.mortar is not None:
                atkData.mortar.writeXML(builder.mortar)
            if atkData.decidedMystery is not None:
                builder.mystery(atkData.decidedMystery)
                if atkData.decidedMystery == "EARTH" and user.player is not None:
                    bResult = builder.mysteryResult
                    for piece in user.player.pieces:
                        bResult.item(str(piece.item.id))
                elif atkData.decidedMystery == "MOON":
                    bResult = builder.mysteryResult
                    for player in self.room.players:
                        assert player.assistant is not None
                        bPlayer = bResult.player
                        bPlayer.name(player.name)
                        bPlayer.assistantType(player.assistant.type)
            if atkData.pieceList[0].item.attackKind == "EXCHANGE" and atkData.decidedExchange is not None:
                builder.power(key="HP")(str(atkData.decidedExchange["HP"]))
                builder.power(key="MP")(str(atkData.decidedExchange["MP"]))
                builder.power(key="YEN")(str(atkData.decidedExchange["YEN"]))
            if atkData.assistantType is not None:
                builder.assistantType(atkData.assistantType)
            builder.commander.name(atkData.attacker.name)
            if not atkData.isAction:
                builder.target.name(atkData.defender.name)
            if atkData.decidedHP is not None:
                builder.commandChain.hp(str(atkData.decidedHP))
            if atkData.decidedAssistant is not None:
                builder.commandChain.assistantType(atkData.decidedAssistant) # Reset Attack order every 7 ou 5 innings (before send start inning)? or after summom?
            if atkData.attacker == atkData.defender and atkData.decidedPiece is not None:
                atkData.decidedPiece.writeXML(builder.commandChain.piece)
            user.sendXml(builder)

        if not missed:
            if atkData.attacker != atkData.defender and atkData.defender.aiProcessor is not None:
                return self.defenderCommand(atkData.defender, atkData.defender.aiProcessor.onDefenseTurn())
        else:
            print("Attack missed!")

        return endInning

    def inflictDamage(self, atkData: AttackData) -> bool:
        assert self.currentAttack is not None

        hasDamaged = atkData.damage > 0
        chain = False
        print(f"InflictDamage: {atkData}")

        for piece in atkData.pieceList:
            item = piece.item
            if item.attackKind == "DISCARD":
                assert atkData.attacker == atkData.defender
                discardPieceList = [p for p in atkData.pieceList if p.item != item]
                for discardPiece in discardPieceList:
                    if discardPiece.item.attackExtra == "MORTAR":
                        continue
                    atkData.attacker.discardPiece(discardPiece)
                break
            elif item.attackKind == "EXCHANGE":
                assert atkData.attacker == atkData.defender
                assert atkData.decidedExchange is not None
                atkData.attacker.hp = atkData.decidedExchange["HP"]
                atkData.attacker.mp = atkData.decidedExchange["MP"]
                atkData.attacker.yen = atkData.decidedExchange["YEN"]
                break
            elif item.attackKind == "SELL":
                assert len(atkData.pieceList) == 2
                sellItem = atkData.pieceList[1].item
                print("Force buy:", sellItem)
                atkData.defender.decreaseYen(sellItem.price)
                atkData.defender.dealItem(sellItem.id, True)
                atkData.attacker.increaseYen(sellItem.price)
                break
            elif item.attackKind == "ADD_ITEM":
                assert len(atkData.pieceList) == 2
                addItem = atkData.pieceList[1].item
                print("Force deal item:", addItem)
                atkData.defender.dealItem(addItem.id, True)
                break

            elif item.attackKind == "BUY":
                chain = True
                self.currentAttack.decidedPiece = atkData.decidedPiece = atkData.defender.getRandomPiece()
                print(f"Decided item for \"{atkData.defender.name}\": {atkData.decidedPiece}")
                break
            elif item.attackKind == "REMOVE_ITEMS":  # Sweep away 1 item
                chain = True
                self.currentAttack.decidedPiece = atkData.decidedPiece = atkData.defender.getRandomPiece()
                print(f"Decided item for \"{atkData.defender.name}\": {atkData.decidedPiece}")
                if atkData.decidedPiece is not None:
                    atkData.defender.discardPiece(atkData.decidedPiece)
                break
            elif item.attackKind == "REMOVE_ABILITIES": # Forget 1 miracle
                chain = True
                randomItem = self.server.itemManager.getItem(atkData.defender.getRandomMagic())
                self.currentAttack.decidedPiece = atkData.decidedPiece = CommandPiece(randomItem) if randomItem.id != 0 else None
                print(f"Decided item for \"{atkData.defender.name}\": {atkData.decidedPiece}")
                if atkData.decidedPiece is not None:
                    itemId = atkData.decidedPiece.item.id
                    atkData.decidedPiece.abilityIndex = atkData.defender.magics.index(itemId)
                    atkData.defender.discardMagic(itemId)
                    for player in self.room.players:
                        if player in [atkData.defender, atkData.attacker]:
                            continue
                        if player.aiProcessor is not None:
                            player.aiProcessor.notifyMagicDiscard(atkData.defender, itemId)
                break

            if item.attackKind == "INCREASE_HP":
                atkData.defender.increaseHP(item.value)
            elif item.attackKind == "INCREASE_MP":
                if atkData.decidedValue is not None:
                    assert atkData.isCounter
                    atkData.attacker.increaseMP(atkData.decidedValue)
                else:
                    atkData.defender.increaseMP(item.value)
                if item.isAtkHarm():
                    atkData.defender.addHarm(item.attackExtra)
            elif item.attackKind == "INCREASE_YEN":
                atkData.defender.increaseYen(item.value)
            elif item.attackKind == "ABSORB_YEN":
                if atkData.decidedValue is not None:
                    assert atkData.isCounter
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
                atkData.defender.assistant = Assistant(atkData.defender, atkData.decidedAssistant)
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
                atkData.defender.takeDamage(999)
            else:
                if "ABSORB_HP" in atkData.extra:
                    atkData.attacker.increaseHP(atkData.damage)
                if "DAMAGE_TO_SELF" in atkData.extra:
                    atkData.attacker.takeDamage(atkData.damage)
                atkData.defender.takeDamage(atkData.damage)

        return chain

    def attackerCommand(self, player: Player, pieceList: list[CommandPiece], target: Player, decidedExchange: Optional[dict[str, int]] = None):
        if self.currentAttack is None:
            assert player == self.attacker
        else:
            assert player == self.currentAttack.attacker

        print("New Attacker Command!")
        print(f"Used: {pieceList}")

        newAttack = AttackData(player, target, pieceList)
        newAttack.decidedExchange = decidedExchange
        self.queueAttack(newAttack)

    # TODO: Maybe divide defense handing in different classes, like CommandChain, DefenseCommand, Attribute and etc...
    def defenderCommand(self, player: Player, pieceList: list[CommandPiece]) -> bool:
        assert self.currentAttack is not None

        atkData = self.currentAttack.clone()
        assert player == atkData.defender

        print("New Defender Command!")
        print("Used:", str(pieceList))

        self.convertPiecesToOwnedPieces(player, pieceList)
        print("Used (Owned):", str(pieceList))

        magicFreeIdxList: list[int] = []
        for idx, piece in enumerate(pieceList):
            if idx > 0 and piece.item.attackExtra == "MAGIC_FREE":
                assert idx - 1 not in magicFreeIdxList
                magicFreeIdxList.append(idx - 1)
                break

        blocked = False
        reflected = False
        flicked = False

        usedMagic = False
        defenseAttr: Optional[str] = None

        for idx, piece in enumerate(pieceList):
            item = piece.item
            isMagicFree = idx in magicFreeIdxList

            if piece.isAbility:
                player.useMagic(item.id, isMagicFree)
            else:
                player.usePiece(piece, isMagicFree)
            player.deal += 1

            if item.type == "MAGIC":
                usedMagic = True

            if item.id == 195:  # REMOVE_ATTRIBUTE
                atkData.attribute = ""
                self.currentAttack.attribute = ""

            if usedMagic and item.attackExtra == "MAGIC_FREE":
                continue

            if defenseAttr is None or defenseAttr == "LIGHT":
                defenseAttr = item.attribute
            elif defenseAttr != item.attribute and item.attribute != "LIGHT":
                defenseAttr = ""

            if (item.defenseExtra == "REFLECT_WEAPON" and atkData.pieceList[0].item.type == "WEAPON") or\
               (item.defenseExtra == "REFLECT_MAGIC" and atkData.pieceList[0].item.type == "MAGIC") or\
                item.defenseExtra == "REFLECT_ANY":
                reflected = True
                print("Current Attack Reflected!")
                self.currentAttack.attacker, self.currentAttack.defender = self.currentAttack.defender, self.currentAttack.attacker
                atkData = self.currentAttack.clone()
                break
            elif (item.defenseExtra == "FLICK_WEAPON" and atkData.pieceList[0].item.type == "WEAPON") or\
                 (item.defenseExtra == "FLICK_MAGIC" and atkData.pieceList[0].item.type == "MAGIC"):
                flicked = True
                print("Current Attack Flicked!")
                self.currentAttack.attacker, self.currentAttack.defender = self.currentAttack.defender, self.room.getRandomAlive()
                atkData = self.currentAttack.clone()
                break
            elif (item.defenseExtra == "BLOCK_WEAPON" and atkData.pieceList[0].item.type == "WEAPON") or\
                 (item.defenseExtra == "BLOCK_MAGIC" and atkData.pieceList[0].item.type == "MAGIC"):
                blocked = True
                print("Current Attack Blocked!")
                break
            if item.defenseKind == "DFS":
                if item.isDefHarm():
                    atkData.defender.addHarm(item.defenseExtra)

                defense = item.getDef()
                atkData.damage = max(0, atkData.damage - defense)

        chain = False
        if not reflected and not flicked and not blocked:
            # Check if that attack could really be defended
            if len(pieceList) > 0:
                assert Item.checkDefense(atkData.attribute, defenseAttr), f"Invalid defense used! (Attack Attr: {atkData.attribute}, Def Attr: {defenseAttr})"

            if atkData.damage > 0:
                for piece in pieceList:
                    item = piece.item
                    if item.defenseKind != "COUNTER":
                        continue
                    print("Counter attack!")
                    target = atkData.attacker if item.attackKind != "INCREASE_MP" else atkData.defender
                    newAttack = AttackData(atkData.defender, target, [piece])
                    piece.illusionItem = None
                    if item.id in [187, 194]: # FIRE ATK, ABSORB_YEN
                        newAttack.decidedValue = atkData.damage
                    elif item.id in [190, 193]: # SOIL ATK (x2), INCREASE_MP (x2)
                        newAttack.decidedValue = atkData.damage * 2
                    newAttack.isCounter = True
                    self.queueAttack(newAttack, True)

            chain = self.inflictDamage(atkData)
            if atkData.attacker == atkData.defender:
                print("Self attack, no defense!")
                return True
            if atkData.mortar is not None:
                print("Mortar attack, no defense!")
                return True

        builder = XMLBuilder("COMMAND")

        for player in self.room.players:
            if player in [atkData.defender, atkData.attacker]:
                continue
            if player.aiProcessor is not None:
                player.aiProcessor.notifyAttack(atkData, pieceList, reflected or blocked or flicked)

        if not reflected and atkData.decidedPiece is not None:
            atkData.decidedPiece.writeXML(builder.commandChain.piece)
        elif not chain:
            for piece in pieceList:
                piece.writeXML(builder.piece)

        if reflected or flicked:
            builder.target.name(str(atkData.defender.name))

        if atkData.decidedValue is not None:
            builder.decidedValue(str(atkData.decidedValue))

        self.room.broadXml(builder)

        if reflected or blocked or flicked:
            # Check if that attack could really be defended
            if pieceList[0].item.defenseExtra != "REFLECT_ANY" and atkData.pieceList[0].item.type != "MAGIC":
                assert Item.checkDefense(atkData.attribute, defenseAttr), f"Invalid defense used! (Attack Attr: {atkData.attribute}, Def Attr: {defenseAttr})"

            if blocked or atkData.defender.dead:
                return True
            elif atkData.attacker == atkData.defender:
                self.inflictDamage(atkData)
                return True
            elif atkData.defender.aiProcessor is not None:
                return self.defenderCommand(atkData.defender, atkData.defender.aiProcessor.onDefenseTurn())
            return False

        if atkData.pieceList[0].item.attackKind == "BUY":
            if atkData.decidedPiece is None or atkData.attacker.yen < atkData.decidedPiece.item.price:
                return True
            else:
                if atkData.attacker.aiProcessor is not None:
                    self.playerBuyResponse(atkData.attacker, atkData.attacker.aiProcessor.getBuyResponse(atkData.decidedPiece.item))
                    return True
                return False

        return True
