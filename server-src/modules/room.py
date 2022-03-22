# -*- coding: cp1252 -*-
from __future__ import annotations
from typing import TYPE_CHECKING, Any, Optional
if TYPE_CHECKING:
    from server import Server
    from modules.session import Session
from helpers.xmlbuilder import XMLBuilder
from modules.player import Player
from modules.turn import TurnHandler
from modules.attack import AttackData

import random
from twisted.internet import reactor

__all__ = ("Room",)


class Room:
    server: Server
    serverMode: str
    id: int
    name: str
    password: str
    language: str
    playersLimit: int
    time: int
    fast: bool
    playing: bool
    inningCount: int
    attackOrderList: list[Player]
    attackOrder: int
    ended: bool
    handledDiseaseThisTurn: bool
    handledAssistantThisTurn: bool
    teamPlay: bool
    turn: TurnHandler
    forceNextDeal: Optional[int]
    forceInitialDeal: Optional[list[int]]
    forceNextAssistant: Optional[str]
    users: list[Session]
    players: list[Player]
    timeoutTimer: Any

    __slots__ = tuple(__annotations__)

    def __init__(self, server: Server, name: str, password: str = ""):
        self.server = server
        self.serverMode = str()

        self.id = int()
        self.name = name
        self.password = password
        self.language = str()
        self.playersLimit = int()
        self.time = int()
        self.fast = bool()
        self.playing = bool()
        self.inningCount = -1
        self.attackOrderList = list()
        self.attackOrder = -1
        self.ended = bool()
        self.handledDiseaseThisTurn = bool()
        self.handledAssistantThisTurn = bool()

        self.teamPlay = bool()

        self.turn = TurnHandler(self)

        self.forceNextDeal = None
        self.forceInitialDeal = None
        self.forceNextAssistant = None

        self.users = list()
        self.players = list()

        self.timeoutTimer = None

    def broadXml(self, xml):
        for user in self.users:
            user.sendXml(xml)

    def sendChat(self, sender: str, msg: str):
        builder = XMLBuilder("CHAT")
        builder.name(sender)
        builder.comment(msg)
        self.broadXml(builder)

    def getPlayer(self, name: str) -> Optional[Player]:
        for player in self.players:
            if player.name == name:
                return player
        return None

    def getRandomAlive(self, me: Optional[Player] = None) -> Player:
        return random.choice([player for player in self.players if not player.dead and player != me])

    def getRandomAliveEnemy(self, me: Player) -> Player:
        return random.choice([player for player in self.players if not player.dead and player.isEnemy(me)])

    def getRandomAliveAlly(self, me: Player, exceptMe: bool = True) -> Player:
        return random.choice([player for player in self.players if not player.dead and (not exceptMe or player != me) and not player.isEnemy(me)])

    def getAliveCount(self) -> int:
        return sum(not player.dead for player in self.players)

    def getAliveTeams(self) -> list[str]:
        aliveTeams = []
        for player in self.players:
            if not player.dead and player.team not in aliveTeams:
                aliveTeams.append(player.team)
        return aliveTeams

    def getTeamsAliveCount(self) -> int:
        return len(self.getAliveTeams())

    def areEnemiesAlive(self, me: Player) -> bool:
        return any(player.isEnemy(me) and not player.dead for player in self.players)

    def checkEndGame(self) -> bool:
        getAliveCount = self.getTeamsAliveCount if self.teamPlay else self.getAliveCount
        return getAliveCount() <= 1

    def addUser(self, user: Session, roomCreate: bool = False):
        builder = XMLBuilder("ENTER")
        
        bRoom = builder.room
        for user_ in self.users:
            bUser = bRoom.user
            bUser.name(user_.name)
        bRoom.name(self.name)
        bRoom.playersLimit(str(self.playersLimit))
        if self.fast:
            bRoom.isFast  # <isFast />
        
        bGame = bRoom.game  # <game />
        if len(self.players) > 0:
            if self.playing:
                bGame.inningCount(str(self.inningCount + 1))
            if self.ended:
                bGame.isEnded
            bPlayers = bGame.players
            for player in self.players:
                bPlayer = bPlayers.player
                bPlayer.name(player.name)
                bPlayer.team(player.team)
                if player.ready:
                    bPlayer.isReady  # <isReady />
                if player.dead:
                    bPlayer.isDead  # <isDead />
                if player.lost:
                    bPlayer.isLost
                if player.finished:
                    bPlayer.isFinished
                if player.waitingAttackTurn:
                    bPlayer.isWaitingAttackTurn
                bPlayer.power(key="HP")(str(player.hp))
                bPlayer.power(key="MP")(str(player.mp))
                bPlayer.power(key="YEN")(str(player.yen))
                if player.disease:
                    bPlayer.disease(player.disease)
                for harm in player.harms:
                    bPlayer.harm(harm)
                if player.assistantType:
                    bAssistant = bPlayer.assistant
                    bAssistant.type(player.assistantType)
                    bAssistant.hp(str(player.assistantHP))
        
        if self.playing:
            privPlayer = self.getPlayer(user.name)
            if privPlayer is not None:
                bGame.dealCount(str(privPlayer.deal))
                bPrivPlayer = bGame.privatePlayer
                bPrivPlayer.time("1475196662616")
                for item in privPlayer.items:
                    # TODO: Illusion
                    bPrivPlayer.item.item(str(item))
                for idx, item in enumerate(privPlayer.magics):
                    bAbility = bPrivPlayer.ability
                    bAbility.item(str(item))
                    bAbility.abilityIndex(str(idx))
            
            bAttacker = bGame.attacker
            if self.turn.currentAttack is None:
                bAttacker.name(str(self.turn.attacker.name))
            else:
                atkData = self.turn.currentAttack

                # TODO: maybe this code could be improved if we somehow saved a copy of the turn xml builder and used it here...
                # TODO: retargeted attacks appears as normal attacks... idk if there's any way to fix this
                bAttacker.name(str(atkData.attacker.name))
                bCommand = bGame.COMMAND
                for item in atkData.piece:
                    bPiece = bCommand.piece
                    bPiece.item(str(item.id))
                    if item.attackExtra == "MAGICAL":
                        bPiece.costMP(str(atkData.damage // 2))
                    if item.assistantType:
                        bPiece.assistantType(item.assistantType)
                if atkData.decidedValue is not None:
                    bCommand.decidedValue(str(atkData.decidedValue))
                if atkData.decidedMystery is not None:
                    builder.mystery(atkData.decidedMystery)
                if atkData.assistantType is not None:
                    builder.assistantType(atkData.assistantType)
                bCommand.commander.name(atkData.attacker.name)
                if not atkData.isAction:
                    bCommand.target.name(atkData.defender.name)
                if atkData.decidedHP is not None:
                    builder.commandChain.hp(str(atkData.decidedHP))
                if atkData.decidedAssistant is not None:
                    builder.commandChain.assistantType(atkData.decidedAssistant)
                if atkData.attacker == atkData.defender and atkData.decidedItem is not None:
                    bPiece = builder.commandChain.piece
                    bPiece.item(str(atkData.decidedItem.id))
                    if atkData.abilityIndex is not None:
                        bPiece.abilityIndex(str(atkData.abilityIndex))

        user.sendXml(builder)

        user.state = "ROOM"
        self.users.append(user)

        builder = XMLBuilder("ADD_USER")
        builder.user.name(user.name)
        self.broadXml(builder)

        # For Broadcasting to Lobby
        if roomCreate:
            bRoom = builder.room
            bRoom.name(self.name)
            bRoom.id(str(self.id))
            bRoom.language(self.language)
            bRoom.playersLimit(str(self.playersLimit))
            if self.fast:
                bRoom.isFast(str(self.fast))
            bRoom.time(str(self.time))
        else:
            builder.roomID(str(self.id))

        self.server.lobbyBroadXml(builder)

    def removeUser(self, user: Session):
        if user not in self.users:
            return

        self.users.remove(user)

        if len(self.users) == 0:
            # Destroy Room
            del self.server.rooms[self.id]
        else:
            builder = XMLBuilder("REMOVE_USER")
            builder.name(user.name)
            self.broadXml(builder)

        # Broadcast to Lobby
        builder = XMLBuilder("REMOVE_USER")
        builder.roomID(str(self.id))
        builder.user.name(user.name)
        self.server.lobbyBroadXml(builder)

    def enterGame(self, user: Session, team: str):
        assert team in ["SINGLE", "TEAM1", "TEAM2", "TEAM3", "TEAM4"]
        if self.playing:
            return

        player = self.getPlayer(user.name)

        if len(self.players) == 0:
            self.teamPlay = team != "SINGLE"
        else:
            assert self.teamPlay == (team != "SINGLE"), "Player tried to choose an impossible team"

        if player is None:
            player = Player(user, user.name, team)
            self.players.append(player)
        else:
            player.team = team

        print(f"Add player: {user.name}@{team}")

        builder = XMLBuilder("ADD_PLAYER")
        bPlayer = builder.player
        bPlayer.name(player.name)
        bPlayer.team(player.team)
        self.broadXml(builder)

        # Broadcast to Lobby
        builder.roomID(str(self.id))
        self.server.lobbyBroadXml(builder)

        return player

    def exitGame(self, player: Player):
        if player not in self.players:
            return

        print("Remove player:", player.name)

        if self.playing:
            player.session = None
            player.enableAIProcessor()
            assert player.aiProcessor is not None

            endInning = False
            atkData = self.turn.currentAttack
            if atkData is None:
                if self.turn.attacker == player:
                    self.turn.queueAttack(player.aiProcessor.onAttackTurn())
                    endInning = True
            elif atkData.defender == player:
                endInning = self.turn.defenderCommand(player, player.aiProcessor.onDefenseTurn())
            
            if endInning:
                self.nextInning()
        else:
            self.players.remove(player)

            builder = XMLBuilder("REMOVE_PLAYER")
            builder.player.name(player.name)
            self.broadXml(builder)

            builder.roomID(str(self.id))
            self.server.lobbyBroadXml(builder)

    def playerReady(self, playerName: str):
        if self.playing:
            return

        builder = XMLBuilder("ADD_PLAYER")
        bPlayer = builder.player
        bPlayer.name(playerName)
        bPlayer.isReady
        self.broadXml(builder)

        if len(self.players) < 2:
            return

        for player in self.players:
            if not player.ready:
                return

        self.startGame()

    def startGame(self):
        assert len(self.players) > 0, "StartGame called without players."
        if self.playing:
            return
        
        self.inningCount = -1
        self.playing = True
        self.ended = False
        self.handledDiseaseThisTurn = True
        self.handledAssistantThisTurn = True
        
        for player in self.players:
            player.reset()
            player.ready = True

        self.attackOrder = -1

        builder = XMLBuilder("START_GAME")
        self.broadXml(builder)
        
        builder.roomID(str(self.id))
        builder.time(str(self.time))
        self.server.lobbyBroadXml(builder)

        self.nextInning()

    def endGame(self):
        self.playing = False
        self.ended = True

        builder = XMLBuilder("END_GAME")
        self.broadXml(builder)

    def resetAttackOrder(self):
        self.attackOrderList = list(self.players)
        random.shuffle(self.attackOrderList)

        for player in self.players:
            player.waitingAttackTurn = True
        
        builder = XMLBuilder("RESET_ATTACK_ORDER")
        self.broadXml(builder)

    def selectNewAttacker(self) -> Player:
        self.attackOrder = (self.attackOrder + 1) % len(self.players)
        if self.attackOrder == 0:
            self.resetAttackOrder()
        
        next = self.attackOrderList[self.attackOrder]
        while next.dead:
            self.attackOrder = (self.attackOrder + 1) % len(self.players)
            next = self.attackOrderList[self.attackOrder]

        assert next in self.players and not next.dead
        return next

    def handlePlayersDeath(self):
        for player in self.players:
            if player.hp > 0 or player.dead:
                continue
            
            if self.getAliveCount() >= 2 and player.hasItem(244):  # REVIVE
                self.turn.playerDyingAttack(player, self.server.itemManager.getItem(244))
            elif self.getAliveCount() >= 2 and player.hasItem(117):  # DYING_ATTACK
                player.dead = True
                self.turn.playerDyingAttack(player, self.server.itemManager.getItem(117))
            else:
                player.dead = True
                
                if player.team == "SINGLE":
                    player.lost = True
                elif player.team not in self.getAliveTeams():
                    for _player in self.players:
                        if _player.team == player.team:
                            _player.lost = True

                builder = XMLBuilder("DIE")
                builder.player.name(player.name)
                self.broadXml(builder)
        
                builder.roomID(str(self.id))
                self.server.lobbyBroadXml(builder)

    def doPlayersDeals(self):
        for player in self.players:
            print(player.name, "HP:", player.hp, "MP:", player.mp, "YEN:", player.yen, "ITEMS:", len(player.items), "MAGICS:", len(player.magics))
            if player.deal > 0 and not player.dead:
                if player.session is not None:
                    if self.inningCount == -1 and self.forceInitialDeal is not None:
                        for item in self.forceInitialDeal[:player.deal]:
                            player.dealItem(item)
                            player.deal -= 1
                    if self.forceNextDeal is not None:
                        player.dealItem(self.forceNextDeal)
                        player.deal -= 1
                        self.forceNextDeal = None
                items = self.server.itemManager.getProbRandomItems(player.deal)
                for item in items:
                    player.dealItem(item.id)
                player.deal = 0

    def beforeEndInning(self) -> bool:
        self.handlePlayersDeath()
            
        if not self.turn.attackQueue.empty():
            return False
        
        if not self.handledDiseaseThisTurn:
            self.handledDiseaseThisTurn = True
            if not self.turn.attacker.dead and self.turn.attacker.disease:
                gotWorse = False
                if random.randrange(100) < self.turn.attacker.worseChance:
                    gotWorse = True
                    self.turn.attacker.addHarm(self.turn.attacker.disease)
                else:
                    self.turn.attacker.worseChance += 1

                if (gotWorse and self.turn.attacker.hp == 0) or self.turn.attacker.diseaseEffect():
                    builder = XMLBuilder("DISEASE")
                    if gotWorse:
                        builder.worse
                    self.broadXml(builder)

                    if self.turn.attacker.hp <= 0:
                        return self.beforeEndInning()

        if not self.handledAssistantThisTurn and not self.checkEndGame():
            self.handledAssistantThisTurn = True
            for player in self.players:
                if player.dead or not player.assistantType or not player.isEnemy(self.turn.attacker):
                    continue
                
                if random.randrange(100) < 30:
                    print(f"{player.name} assistant attack!")
                    piece = [self.server.itemManager.getProbRandomAssistantItem(player.assistantType)]

                    if player.assistantType == "EARTH":
                        newItem = self.server.itemManager.getProbRandomItems(1)[0]
                        piece.append(newItem)
                        if newItem.type != "MAGIC" and newItem.attackKind != "EXCHANGE":
                            if newItem.attackKind == "SELL":
                                piece = [newItem, self.server.itemManager.getProbRandomItems(1)[0]]
                            elif newItem.attackKind in ["ATK", "BUY"]:
                                piece = [newItem]
                    elif player.assistantType == "MOON":
                        newItem = None
                        # TODO: This should be optimized somehow
                        while newItem is None or newItem.type != "MAGIC" or newItem.defenseExtra == "FLICK_MAGIC" or newItem.defenseExtra == "BLOCK_WEAPON" or newItem.attackKind == "SET_ASSISTANT":
                            newItem = self.server.itemManager.getProbRandomItems(1)[0]
                        if newItem.attackExtra == "WIDE_ATK" or newItem.attackExtra == "DOUBLE_ATK":
                            piece.append(newItem)
                        else:
                            piece = [newItem]
                                
                    target = player
                    if (piece[0].attackKind == "ATK" and piece[0].hitRate == 0) or piece[0].attackKind in ["SELL", "BUY", "ABSORB_YEN", "ADD_HARM", "REMOVE_ITEMS", "REMOVE_ABILITIES"]:
                        target = self.getRandomAliveEnemy(player)
                    elif (piece[0].attackKind == "INCREASE_MP" and not piece[0].isAtkHarm()) or piece[0].attackKind in ["INCREASE_HP", "INCREASE_YEN", "REMOVE_LOWER_HARMS", "REMOVE_ALL_HARMS", "ADD_ITEM", "SET_ASSISTANT"]:
                        target = self.getRandomAliveAlly(player, False)
                        
                    newAttack = AttackData(player, target, piece)
                    newAttack.assistantType = player.assistantType
                    self.turn.queueAttack(newAttack, True)
                    
            return self.turn.attackQueue.empty()

        return True

    def endInning(self):
        while not self.beforeEndInning():
            if not self.turn.doAttack():
                # Player input is required to proceed.
                return False

        print("Round", self.inningCount+1, "ended, starting new round..")

        self.doPlayersDeals()
        
        builder = XMLBuilder("END_INNING")
        self.broadXml(builder)

        return True

    def startInning(self):
        self.turn.new(self.selectNewAttacker())
        self.turn.attacker.waitingAttackTurn = False

        self.inningCount += 1
        self.handledDiseaseThisTurn = False
        self.handledAssistantThisTurn = False
        
        builder = XMLBuilder("START_INNING")
        builder.attacker.name(self.turn.attacker.name)
        self.broadXml(builder)

    def nextInning(self):
        if self.timeoutTimer is not None and self.timeoutTimer.active():
            self.timeoutTimer.cancel()

        while True:
            if not self.endInning():
                # Player input is required to proceed.
                break

            if self.checkEndGame():
                self.endGame()
                return

            self.startInning()
            
            if self.turn.attacker.aiProcessor is not None:
                self.turn.queueAttack(self.turn.attacker.aiProcessor.onAttackTurn())
                continue
            
            # Player input is required to proceed.
            break
        
        if self.turn.attacker.session is not None and self.serverMode != "TRAINING":
            self.timeoutTimer = reactor.callLater(60 * len(self.players), self.turn.attacker.session.user.transport.loseConnection) # type: ignore


