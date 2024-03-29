from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Iterator
if TYPE_CHECKING:
    from server import Server
    from modules.room import Room
    from modules.player import Player
from dataclasses import dataclass
from modules.commandPiece import CommandPiece
from modules.item import Item

from typing import Optional
from enum import Enum
import random

__all__ = ("AIProcessor",)


@dataclass
class EnemyStats:
    lastHP: Optional[int] = None
    damageCombo: int = 0

class PieceScore(Enum):
    DISCARD = 0
    LOWEST = 1
    BELOW_LOW = 2
    LOW = 3
    MEDIUM = 4
    ABOVE_MEDIUM = 5
    HIGH = 6
    CRITICAL = 7

class AIProcessor:
    player: Player
    room: Room
    server: Server
    enemyStats: dict[str, EnemyStats]
    possiblyDefenseless: list[Player]

    __slots__ = tuple(__annotations__)

    def __init__(self, player: Player):
        self.player = player
        self.room = player.room
        self.server = player.server
        self.enemyStats = dict()
        self.possiblyDefenseless = list()

    def checkEnemyStats(self):
        for player in self.room.players:
            if not player.isEnemy(self.player):
                continue

            if player.dead:
                if player in self.possiblyDefenseless:
                    self.possiblyDefenseless.remove(player)
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

                    if stats.damageCombo > 1 and not player in self.possiblyDefenseless:
                        # Possibly defenseless
                        self.possiblyDefenseless.append(player)
                elif stats.lastHP <= player.hp:
                    # Didn't take damage
                    stats.damageCombo = 0

            stats.lastHP = player.hp

        print(f"Enemy Stats: {self.enemyStats}")

    def getPiecesByAK(self, kind: str) -> list[CommandPiece]:
        items: list[CommandPiece] = []
        for piece in self.player.pieces:
            item = piece.getItemOrIllusion()
            if item.type == "MAGIC" and self.player.mp < item.subValue:
                continue
            if item.attackKind == kind:
                items.append(piece)
        return items

    def getPiecesByAE(self, extra: str, attr: Optional[str] = None) -> list[CommandPiece]:
        items: list[CommandPiece] = []
        for piece in self.player.pieces:
            item = piece.getItemOrIllusion()
            if item.type == "MAGIC" and self.player.mp < item.subValue:
                continue
            if attr is not None and item.attribute != attr:
                continue
            if item.attackExtra == extra:
                items.append(piece)
        for id in self.player.magics:
            item = self.server.itemManager.getItem(id)
            if self.player.mp < item.subValue:
                continue
            if attr is not None and item.attribute != attr:
                continue
            if item.attackExtra == extra:
                items.append(CommandPiece(item, True))
        return items

    def getPiecesDamage(self, damage: int, pieces: list[CommandPiece]) -> int:
        for idx, piece in enumerate(pieces):
            item = piece.getItemOrIllusion()
            if idx > 0 and item.attackExtra == "MAGIC_FREE" and pieces[idx - 1].item.type == "MAGIC":
                continue
            if item.attackExtra == "MAGICAL":
                damage = self.player.mp * 2
            elif item.attackExtra == "DOUBLE_ATK":
                damage *= 2
            else:
                damage += item.getAtk()
        return damage

    def getDefensePieces(self, forAttribute: str) -> list[CommandPiece]:
        pieces: list[CommandPiece] = []
        for piece in self.player.pieces:
            item = piece.getItemOrIllusion()
            if item.defenseKind != "DFS":
                continue
            if item.type == "MAGIC" and self.player.mp < item.subValue:
                continue
            if not Item.checkDefense(forAttribute, item.attribute):
                continue
            pieces.append(piece)
        for id in self.player.magics:
            item = self.server.itemManager.getItem(id)
            if item.defenseKind != "DFS":
                continue
            if self.player.mp < item.subValue:
                continue
            if not Item.checkDefense(forAttribute, item.attribute):
                continue
            pieces.append(CommandPiece(item, True))
        return sorted(pieces, key = lambda x: x.getItemOrIllusion().getDef())

    def getCounterRings(self, forAttribute: str) -> list[CommandPiece]:
        items: list[CommandPiece] = []
        harms: list[str] = []
        for piece in self.player.pieces:
            item = piece.getItemOrIllusion()
            if item.defenseKind != "COUNTER" or (item.isAtkHarm() and item.attackExtra in harms):
                continue
            if not Item.checkDefense(forAttribute, item.attribute):
                continue
            if item.isAtkHarm():
                harms.append(item.attackExtra)
            items.append(piece)
        return items

    def getCounterPieces(self, forAttribute: Optional[str], isCounterAttack: bool, isMagicAttack: bool, isWeaponAttack: bool) -> list[CommandPiece]:
        items: list[CommandPiece] = []
        for piece in self.player.pieces:
            item = piece.getItemOrIllusion()
            if item.type == "MAGIC" and self.player.mp < item.subValue:
                continue
            if item.defenseExtra == "REFLECT_ANY":
                items.append(piece)
            if (not item.hasSpecialMagicDefense() or not isMagicAttack) and \
                (not item.hasSpecialWeaponDefense() or not isWeaponAttack):
                continue
            if forAttribute is None or forAttribute == "DARK" or isCounterAttack:
                continue
            elif "WEAPON" in item.defenseExtra and not Item.checkDefense(forAttribute, item.attribute):
                continue
            items.append(piece)
        for id in self.player.magics:
            item = self.server.itemManager.getItem(id)
            if self.player.mp < item.subValue:
                continue
            if item.defenseExtra == "REFLECT_ANY":
                items.append(CommandPiece(item, True))
            if (not item.hasSpecialMagicDefense() or not isMagicAttack) and \
                (not item.hasSpecialWeaponDefense() or not isWeaponAttack):
                continue
            if forAttribute is None or forAttribute == "DARK" or isCounterAttack:
                continue
            elif "WEAPON" in item.defenseExtra and not Item.checkDefense(forAttribute, item.attribute):
                continue
            items.append(CommandPiece(item, True))
        return items

    def checkIsItemBadToSell(self, item: Item) -> bool:
        reallyNeedsMoney = self.player.hp <= 14 and self.player.yen <= 2

        # Magics
        if item.type == "MAGIC":
            return True

        # Healers
        if item.attackKind in ["INCREASE_HP", "INCREASE_MP"]:
            return True
        elif item.attackKind in ["REMOVE_ALL_HARMS"]:
            if self.player.hasDisease() or not reallyNeedsMoney:
                return True
        elif item.attackKind in ["REMOVE_LOWER_HARMS"]:
            if self.player.hasLowerDisease() or not reallyNeedsMoney:
                return True

        # Goods
        if item.attackExtra in ["SET_ASSISTANT", "ADD_ATTRIBUTE", "INCREASE_ATK", "MAGIC_FREE", "REVIVE", "DYING_ATTACK"]:
            return True

        # Counters
        if item.defenseKind in ["COUNTER"] or \
            item.defenseExtra in ["REFLECT_ANY"]:
            return True

        return False

    def getMaxMPForMagic(self, target: Player) -> int:
        maxMP = 0
        for id in target.magics:
            item = self.server.itemManager.getItem(id)
            maxMP = max(item.subValue, maxMP)
        for item in target.getItems(False):
            if item.type == "MAGIC":
                maxMP = max(item.subValue, maxMP)
        return maxMP

    def getAllies(self) -> Iterator[Player]:
        yield self.player
        if self.player.team != "SINGLE":
            for player in self.room.players:
                if player != self.player and not player.dead and not player.isEnemy(self.player):
                    yield player

    def getEnemies(self) -> Iterator[Player]:
        for player in self.room.players:
            if not player.dead and player.isEnemy(self.player):
                yield player

    def getAttackAttribute(self, pieces: list[CommandPiece]) -> Optional[str]:
        attribute = None
        usedMagic = False
        for piece in pieces:
            item = piece.getItemOrIllusion()
            if usedMagic and item.attackExtra == "MAGIC_FREE":
                continue
            if attribute is None or attribute == "LIGHT" or item.attackExtra == "ADD_ATTRIBUTE":
                attribute = item.attribute
            elif attribute != item.attribute and item.attribute != "LIGHT":
                attribute = ""
            if item.type == "MAGIC":
                usedMagic = True
        return attribute

    def canBeInstantlyKilledBy(self, defender: Player, pieceOrPieces: CommandPiece | list[CommandPiece], overrideDamage: Optional[int] = None) -> bool:
        if type(pieceOrPieces) is CommandPiece:
            item = pieceOrPieces.getItemOrIllusion()
            if defender.disease == "HEAVEN" and item.attackExtra in Item.ALL_DISEASES:
                return True
            if not item.attribute:
                return False
            # TODO: This needs to be improved to also check item combinations
            return defender.hp <= (item.getAtk() if overrideDamage is None else overrideDamage)
        elif type(pieceOrPieces) is list:
            damage = 0
            attribute = None
            harms = []
            usedMagic = False
            for piece in pieceOrPieces:
                item = piece.getItemOrIllusion()
                if usedMagic and item.attackExtra == "MAGIC_FREE":
                    continue
                damage += item.getAtk()
                if item.attackExtra == "MAGICAL":
                    damage = self.player.mp * 2
                if item.attackExtra == "DOUBLE_ATK":
                    damage *= 2
                if attribute is None or attribute == "LIGHT" or item.attackExtra == "ADD_ATTRIBUTE":
                    attribute = item.attribute
                elif attribute != item.attribute and item.attribute != "LIGHT":
                    attribute = ""
                if item.isAtkHarm():
                    harms.append(item.attackExtra)
                if item.type == "MAGIC":
                    usedMagic = True
            assert damage == overrideDamage, f"Damage mismatch! {damage} != {overrideDamage} (Items: {repr(pieceOrPieces)})"
            if defender.disease == "HEAVEN" and any(harm in harms for harm in Item.ALL_DISEASES):
                return True
            if not attribute:
                return False
            return defender.hp <= damage
        else:
            raise NotImplementedError()

    def convertOwnedPiecesToPieces(self, pieceList: list[CommandPiece]):
        for idx, attackPiece in enumerate(pieceList):
            if attackPiece.illusionItem is None:
                pieceList[idx] = CommandPiece(attackPiece.item, attackPiece.isAbility)
                continue
            illusionIndex = 0
            for piece in self.player.pieces:
                if piece == attackPiece:
                    illusionPiece = CommandPiece(attackPiece.illusionItem)
                    illusionPiece.illusionItemIndex = illusionIndex
                    pieceList[idx] = illusionPiece
                    break
                if piece.illusionItem is not None and piece.illusionItem.id == attackPiece.illusionItem.id:
                    illusionIndex += 1
            assert pieceList[idx].illusionItem is None

    def onAttackTurn(self) -> tuple[list[CommandPiece], Player, Optional[dict[str, int]]]:
        target, pieceList = self.buildAttack()
        self.convertOwnedPiecesToPieces(pieceList)
        decidedExchange = self.buildExchange() if pieceList[0].item.attackKind == "EXCHANGE" else None
        return pieceList, target, decidedExchange

    def buildAttackPossibilityScores(self) -> dict[PieceScore, list[tuple[Player, CommandPiece | list[CommandPiece]]]]:
        scores: dict[PieceScore, list[tuple[Player, CommandPiece | list[CommandPiece]]]] = dict((score, []) for score in PieceScore)

        def buildMagicScore(piece: CommandPiece, isBound: bool):
            item = piece.item
            magicFree = self.getPiecesByAE("MAGIC_FREE")
            if self.player.mp < item.subValue and len(magicFree) == 0:
                return

            # Avoid spamming magics with a low hit rate.
            if isBound and 0 < item.hitRate < random.randrange(1, 100 + 1):
                return

            # These items can't be used here
            if item.attackExtra in ["WIDE_ATK", "DOUBLE_ATK"] or\
               item.defenseExtra in ["FLICK_MAGIC", "BLOCK_WEAPON"]:
                return

            if item.attackKind == "INCREASE_YEN":
                if self.player.yen >= 50:
                    if isBound:
                        return
                    score = PieceScore.LOW
                else:
                    score = PieceScore.MEDIUM
                if self.player.mp < item.subValue:
                    scores[score].append((self.player, [piece, random.choice(magicFree)]))
                else:
                    scores[score].append((self.player, piece))
                return

            if item.attackKind in ["SET_ASSISTANT", "INCREASE_HP", "REMOVE_ALL_HARMS", "REMOVE_LOWER_HARMS"]:
                for ally in self.getAllies():
                    score = PieceScore.LOW

                    if item.attackKind == "SET_ASSISTANT":
                        if ally.assistant is not None:
                            if isBound:
                                continue
                            score = PieceScore.DISCARD
                        else:
                            score = PieceScore.ABOVE_MEDIUM

                    elif item.attackKind == "INCREASE_HP":
                        score = PieceScore.LOW if ally.hp >= 25 else PieceScore.CRITICAL

                    elif item.attackKind == "REMOVE_ALL_HARMS":
                        if not ally.disease:
                            if isBound:
                                continue
                            score = PieceScore.DISCARD
                        else:
                            score = PieceScore.HIGH if ally.disease in ["HELL", "HEAVEN"] else PieceScore.MEDIUM

                    elif item.attackKind == "REMOVE_LOWER_HARMS":
                        if not ally.hasLowerDisease():
                            if isBound:
                                continue
                            score = PieceScore.DISCARD
                        else:
                            score = PieceScore.MEDIUM

                    if score != PieceScore.DISCARD and self.player.mp < item.subValue:
                        scores[score].append((ally, [piece, random.choice(magicFree)]))
                    else:
                        scores[score].append((ally, piece))
            else:
                for target in self.getEnemies():
                    score = PieceScore.MEDIUM

                    if item.attackExtra == "INCREASE_ATK" and item.getAtk() < 10:
                        score = PieceScore.LOW

                    if item.attackKind == "ATK":
                        if self.canBeInstantlyKilledBy(target, piece):
                            score = PieceScore.HIGH
                        elif item.getAtk() >= 10:
                            score = PieceScore.ABOVE_MEDIUM

                    elif item.attackKind == "ADD_HARM":
                        isDisease = item.attackExtra in Item.ALL_DISEASES
                        # TODO: If that could be assured to be possible, we could allow the bot to kill the player by worsening the disease until heaven break.
                        if (isDisease and target.disease == "HELL") or item.attackExtra in target.harms:
                            continue
                        if isDisease and target.disease == "HEAVEN":
                            score = PieceScore.HIGH

                    if self.player.mp < item.subValue:
                        scores[score].append((target, [piece, random.choice(magicFree)]))
                    else:
                        scores[score].append((target, piece))

        for id in self.player.magics:
            item = self.server.itemManager.getItem(id)
            buildMagicScore(CommandPiece(item, True), True)

        for piece in self.player.pieces:
            item = piece.getItemOrIllusion()
            if item.type == "SUNDRY":
                if item.attackExtra in ["REVIVE", "MORTAR"]:
                    # These items can't be used for direct attacks, and shouldn't be discarded.
                    continue

                if item.attackExtra in ["INCREASE_ATK", "MAGIC_FREE"]:
                    scores[PieceScore.DISCARD].append((self.player, piece))
                    continue

                if item.attackKind in ["SET_ASSISTANT", "INCREASE_HP", "INCREASE_MP", "REMOVE_ALL_HARMS", "REMOVE_LOWER_HARMS"]:
                    for ally in self.getAllies():
                        score = PieceScore.DISCARD

                        if item.attackKind == "SET_ASSISTANT":
                            if ally.assistant is None:
                                score = PieceScore.ABOVE_MEDIUM

                        elif item.attackKind == "INCREASE_HP":
                            score = PieceScore.LOW if ally.hp >= 25 else PieceScore.CRITICAL

                        elif item.attackKind == "INCREASE_MP":
                            score = PieceScore.LOW if ally.mp >= self.getMaxMPForMagic(ally) else PieceScore.MEDIUM

                        elif item.attackKind == "REMOVE_ALL_HARMS":
                            if ally.disease:
                                score = PieceScore.HIGH if ally.disease in ["HELL", "HEAVEN"] else PieceScore.MEDIUM

                        elif item.attackKind == "REMOVE_LOWER_HARMS":
                            if ally.hasLowerDisease():
                                score = PieceScore.MEDIUM

                        scores[score].append((ally, piece))
                else:
                    for target in self.getEnemies():
                        score = PieceScore.MEDIUM

                        if item.attackKind == "REMOVE_ABILITIES":
                            if len(target.magics) == 0:
                                score = PieceScore.DISCARD

                        scores[score].append((target, piece))

            elif item.type == "TRADE":
                if item.attackKind == "EXCHANGE":
                    score = PieceScore.DISCARD
                    if self.player.hp > 30 or self.player.mp > 0 or self.player.yen > 0:
                        needsHP = self.player.hp < 20
                        needsMP = self.player.mp < 30 and (self.player.magics or any(item.type == "MAGIC" for item in self.player.getItems(False)))
                        if needsHP or (needsMP and (self.player.yen > 4 or self.player.hp >= 50)):
                            score = PieceScore.CRITICAL if needsHP else PieceScore.MEDIUM
                    scores[score].append((self.player, piece))
                    continue

                for target in self.getEnemies():
                    score = PieceScore.MEDIUM

                    if item.attackKind == "SELL":
                        pieceToSell: Optional[CommandPiece] = None
                        if len(mortar := self.getPiecesByAE("MORTAR")) > 0:
                            # Try to sell mortars when we have one
                            score = PieceScore.MEDIUM
                            pieceToSell = mortar[0]
                        else:
                            deadlyPiece: Optional[CommandPiece] = None
                            mostValuablePiece: Optional[CommandPiece] = None
                            for _piece in self.player.pieces:
                                _item = _piece.getItemOrIllusion()
                                if _piece == piece:
                                    continue
                                if target.hp + target.mp + target.yen <= _item.price and (deadlyPiece is None or deadlyPiece.getItemOrIllusion().price > _item.price):
                                    deadlyPiece = _piece
                                if self.checkIsItemBadToSell(_item):
                                    continue
                                if mostValuablePiece is None or mostValuablePiece.getItemOrIllusion().price < _item.price:
                                    mostValuablePiece = _piece
                            if deadlyPiece is not None:
                                score = PieceScore.HIGH
                                pieceToSell = deadlyPiece
                            elif mostValuablePiece is not None:
                                score = PieceScore.MEDIUM if mostValuablePiece.getItemOrIllusion().price >= 10 else PieceScore.LOW
                                pieceToSell = mostValuablePiece
                            else:
                                # We have no items to sell
                                score = PieceScore.DISCARD
                                pieceToSell = None
                        if pieceToSell is not None:
                            scores[score].append((target, [piece, pieceToSell]))
                            continue

                    elif item.attackKind == "BUY":
                        if self.player.yen == 0:
                            score = PieceScore.DISCARD
                        elif self.player.yen < 5:
                            score = PieceScore.LOW

                    scores[score].append((target, piece))

            elif item.type == "WEAPON":
                if item.attackKind == "ATK":
                    pieces: list[CommandPiece] = []
                    damage = 0

                    for target in self.getEnemies():
                        if item.attackExtra == "DYING_ATTACK":
                            score = PieceScore.LOWEST
                        elif item.attackExtra == "PESTLE":
                            # TODO: Increase chance if we saw that some enemy has the mortar.
                            score = PieceScore.BELOW_LOW if self.room.getAliveCount() <= 2 else PieceScore.LOW
                        elif item.attackExtra == "MAGICAL" and self.player.mp < 7:
                            score = PieceScore.BELOW_LOW
                        elif item.price >= 10 and item.getAtk() == 1 and not item.attribute and not item.attackExtra:
                            score = PieceScore.BELOW_LOW
                        elif item.hitRate > 0:
                            if self.canBeInstantlyKilledBy(target, piece):
                                score = PieceScore.HIGH
                            else:
                                score = PieceScore.MEDIUM if self.room.getAliveCount() <= 2 else PieceScore.ABOVE_MEDIUM
                        else:
                            if len(pieces) == 0:
                                pieces.append(piece)
                                damage = item.getAtk() if item.attackExtra != "MAGICAL" else self.player.mp * 2
                                isSpecialAttr = item.attribute in ["DARK", "LIGHT"] or (item.attribute and (damage >= 4 or item.isAtkHarm()))

                                doubleAtk = self.getPiecesByAE("DOUBLE_ATK")
                                wideAtk = self.getPiecesByAE("WIDE_ATK")[1:]
                                magicFree = self.getPiecesByAE("MAGIC_FREE")
                                mpCost = 0 if item.attackExtra != "MAGICAL" else 99

                                # TODO: Try to make it wait to stack a better attack, like with increase_atk and others extras
                                # TODO: Only override item attribute if we can get a good damage doing so
                                # TODO: If weapon or extras has ADD_HARM, try to stack as much damage as possible

                                def appendPieces(newPieces: list[CommandPiece]):
                                    nonlocal pieces, damage, mpCost
                                    for piece in list(newPieces):
                                        item = piece.getItemOrIllusion()
                                        if item.type != "MAGIC":
                                            if item.attackExtra == "MAGICAL":
                                                mpCost = 99
                                            continue
                                        if item.attackExtra == "INCREASE_ATK" and len(doubleAtk) > 0:
                                            # NOTE: This is a attempt to make the bot avoid wasting MP
                                            newPieces.remove(piece)
                                            continue
                                        mpCost += item.subValue
                                        if mpCost <= self.player.mp:
                                            continue
                                        if len(magicFree) == 0:
                                            mpCost -= item.subValue
                                            newPieces.remove(piece)
                                            continue
                                        newPieces.insert(newPieces.index(piece) + 1, magicFree.pop())
                                    pieces += newPieces
                                    damage = self.getPiecesDamage(damage, newPieces)

                                if item.attackExtra != "INCREASE_ATK":
                                    if isSpecialAttr:
                                        increaseAtkAttrib = self.getPiecesByAE("INCREASE_ATK", item.attribute)
                                        appendPieces(increaseAtkAttrib)
                                    else:
                                        increaseAtk = self.getPiecesByAE("INCREASE_ATK")
                                        appendPieces(increaseAtk)

                                if not isSpecialAttr:
                                    if len(doubleAtk) > 0 and damage >= 10:
                                        appendPieces(doubleAtk)

                                    if item.attackExtra != "ADD_ATTRIBUTE":
                                        addAttribute = self.getPiecesByAE("ADD_ATTRIBUTE")[1:]
                                        appendPieces(addAttribute)

                                    if len(wideAtk) > 0 and damage >= 5 and self.room.getAliveCount() > 2:
                                        appendPieces(wideAtk)

                            #TODO: Also increase score if we can kill the enemy AND we know it doesn't have defense
                            if self.canBeInstantlyKilledBy(target, pieces, damage):
                                score = PieceScore.HIGH
                            elif len(pieces) > 1 and self.getAttackAttribute(pieces):
                                score = PieceScore.ABOVE_MEDIUM
                            elif item.hasSpecialWeaponDefense() or item.hasSpecialMagicDefense():
                                score = PieceScore.LOW
                            elif item.attackExtra in ["INCREASE_ATK", "ADD_ATTRIBUTE", "MAGIC_FREE"]:
                                score = PieceScore.BELOW_LOW
                            else:
                                score = PieceScore.MEDIUM

                        scores[score].append((target, pieces if len(pieces) > 0 else piece))

            elif item.type == "MAGIC":
                buildMagicScore(piece, False)

            elif item.type == "PROTECTOR":
                if item.defenseExtra != "REFLECT_ANY":
                    scores[PieceScore.DISCARD].append((self.player, piece))

        return scores

    def buildAttack(self) -> tuple[Player, list[CommandPiece]]:
        self.checkEnemyStats()

        scores = self.buildAttackPossibilityScores()
        #print("Attack Possibility Scores:", repr(scores))

        discardScoresCopy = list(scores[PieceScore.DISCARD])
        for attack in discardScoresCopy:
            # Prune discard list
            assert type(attack[1]) is CommandPiece
            for _attack in discardScoresCopy:
                assert type(_attack[1]) is CommandPiece
                if attack[0] == _attack[0] or attack[1] != _attack[1] or _attack not in scores[PieceScore.DISCARD]:
                    continue
                scores[PieceScore.DISCARD].remove(_attack)

        for score, attackList in reversed(scores.items()):
            if len(attackList) == 0:
                continue
            if score == PieceScore.DISCARD:
                if len(self.player.pieces) == 16:
                    # Discard two items so we can receive new items in the next turn.
                    print("Bot is full of items! 2 items will be discarded.")
                    possibleDiscard = [attack[1] for attack in attackList]
                    return self.player, [CommandPiece(self.server.itemManager.getItem(1))] + random.sample(possibleDiscard, k = min(2, len(possibleDiscard)))  # type: ignore
            else:
                attack = random.choice(attackList)
                assert attack[1], f"{score}, {repr(attack)}"
                print("Bot target:", attack[0])
                return attack[0], attack[1] if type(attack[1]) is list else [attack[1]]  # type: ignore

        print(f"Bot \"{self.player.name}\" couldn't do anything with it's current items.")
        print(self.player.pieces)

        return self.player, [CommandPiece(self.server.itemManager.getItem(0))]

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

    def onDefenseTurn(self) -> list[CommandPiece]:
        pieceList = self.buildDefense()
        self.convertOwnedPiecesToPieces(pieceList)
        return pieceList

    def buildDefense(self) -> list[CommandPiece]:
        assert(self.room.turn.currentAttack is not None)

        # TODO: Build weighted list with all defense possibilities
        # TODO: Better MP Handling

        ret: list[CommandPiece] = []

        attacker = self.room.turn.currentAttack.attacker
        damage = self.room.turn.currentAttack.damage
        attr = self.room.turn.currentAttack.attribute
        print("Damage:", damage, "| Attr:", attr, "| Attacker:", attacker)

        if damage <= 0:
            # TODO: Try to reflect, flick or block
            return ret

        isCounterAttack = self.room.turn.currentAttack.pieceList[0].item.defenseKind == "COUNTER"
        isMagicAttack = self.room.turn.currentAttack.pieceList[0].item.type == "MAGIC"
        isWeaponAttack = self.room.turn.currentAttack.pieceList[0].item.type == "WEAPON"
        print("Counter:", isCounterAttack, "| Magic:", isMagicAttack, "| Weapon:", isWeaponAttack)

        protectors = self.getDefensePieces(attr) if attr is not None else []
        counters = self.getCounterPieces(attr, isCounterAttack, isMagicAttack, isWeaponAttack)
        lastResortCounter: Optional[CommandPiece] = None

        attrRemoved = False
        if "GLORY" not in self.player.harms and attr and (removeAttributePiece := self.player.getOwnedPieceById(195)) is not None and not protectors and not counters:
            protectors_ne = self.getDefensePieces("")
            counters_ne = self.getCounterPieces("", isCounterAttack, isMagicAttack, isWeaponAttack)
            if protectors_ne or counters_ne:
                # We can use NE protectors or counters, so lets erase the attribute with the wings.
                protectors = protectors_ne
                counters = counters_ne
                attr = ""
                attrRemoved = True
                ret.append(removeAttributePiece)

        if counters:
            # Early counter, we only return here if countering is clearly a good choice.
            for counter in counters:
                isWorthForDamage = damage >= counter.item.getAtk() if counter.item.getAtk() else 10
                if isWorthForDamage or self.player.hp <= 15 or self.player.hp <= damage or attr == "DARK" or any(piece.item.isAtkHarm() for piece in self.room.turn.currentAttack.pieceList):
                    if lastResortCounter is None or "FLICK" in lastResortCounter.item.defenseExtra:
                        lastResortCounter = counter
                if "FLICK" in counter.item.defenseExtra:
                    continue
                attackerCanDie = self.room.turn.currentAttack.attacker.hp <= damage and "REFLECT" in counter.item.defenseExtra
                if damage >= 15 or attackerCanDie or any(piece.item.isAtkHarm() for piece in self.room.turn.currentAttack.pieceList):
                    ret.append(counter)
                    return ret

        if isCounterAttack:
            # This is a counter-attack so we can't use defense items
            return ret

        defPiece: list[CommandPiece] = []
        if attr is not None:
            for piece in protectors:
                item = piece.getItemOrIllusion()
                if attr != "DARK" and item.getDef() > 5:
                    if self.player.hp >= 30 and damage / item.getDef() < 0.5:
                        # Not worth it.
                        continue
                    if self.player.hp > damage and damage / item.getDef() <= 0.4:
                        # Not worth it.
                        continue
                defPiece.append(piece)
                damage -= item.getDef()
                if damage <= 0:
                    break

            if attr == "DARK" and damage > 0:
                damage = 999
            
            if damage > 0 and (lastResortCounter is None or self.player.hp > damage):
                rings = self.getCounterRings(attr)
                if self.player.hp <= damage:
                    # We will die, so let's try to maximize counter efficiency
                    defPiece = rings if len(rings) > 0 else defPiece
                else:
                    ringConditions = {
                        # ItemID: Min Value or Condition
                        187: (4,  lambda piece, ringValue: self.canBeInstantlyKilledBy(attacker, piece, ringValue)), # FIRE ATK
                        190: (8,  lambda piece, ringValue: self.canBeInstantlyKilledBy(attacker, piece, ringValue)), # SOIL ATK (x2)
                        193: (10, lambda _, ringValue:     self.getMaxMPForMagic(self.player) <= ringValue), # INCREASE_MP (x2)
                        194: (5, lambda _, ringValue:     attacker.hp + attacker.mp + attacker.yen <= ringValue) # ABSORB_YEN
                    }

                    for piece in rings:
                        item = piece.getItemOrIllusion()
                        if item.id not in ringConditions:
                            if item.attackKind != "ADD_HARM" or item.attackExtra not in attacker.harms:
                                defPiece.append(piece)
                        else:
                            minValue, condition = ringConditions[item.id]
                            ringValue = damage if item.id not in [190, 193] else damage * 2
                            if ringValue >= minValue or condition(piece, ringValue):
                                defPiece.append(piece)

        ret += defPiece

        if lastResortCounter is not None:
            if len(ret) == (1 if attrRemoved else 0):
                # We have no defense items so let's try to counter if possible.
                ret.append(lastResortCounter)
                return ret
            elif self.player.hp <= damage:
                # We have defense items but we will end up dying anyway...
                for piece in protectors:
                    if piece in ret:
                        ret.remove(piece)
                ret.append(lastResortCounter)
                assert len(ret) == (2 if attrRemoved else 1)
                return ret

        if len(ret) == 1 and attr != "DARK" and ret[0].item.id == 195:
            ret = []
        elif len(ret) > 1 and "GLORY" in self.player.harms:
            ret = ([] if attr != "DARK" else ret[:1]) if ret[0].item.id == 195 else ret[-1:]

        return ret

    def getBuyResponse(self, decidedItem: Item) -> bool:
        # TODO: Improve condition?
        return decidedItem.price < 15

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