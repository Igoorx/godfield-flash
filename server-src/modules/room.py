# -*- coding: cp1252 -*-
from __future__ import annotations
from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from server import Server
    from modules.session import Session
from helpers.xmlbuilder import XMLBuilder
from modules.player import Player
from modules.turn import TurnHandler

import random

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
    fdIncludeBots: bool
    forceNextAssistant: Optional[str]
    users: list[Session]
    players: list[Player]

    VALID_TEAMS = ["TEAM1", "TEAM2", "TEAM3", "TEAM4"]
    __slots__ = tuple(__annotations__)

    def __init__(self, server: Server, serverMode: str, name: str, password: str = ""):
        self.server = server
        self.serverMode = serverMode

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
        self.fdIncludeBots = False
        self.forceNextAssistant = None

        self.users = list()
        self.players = list()

    def broadXml(self, xml):
        for user in self.users:
            user.sendXml(xml)

    def sendChat(self, sender: str, msg: str, toTeam: str):
        builder = XMLBuilder("CHAT")
        builder.name(sender)
        builder.comment(msg)
        if toTeam:
            builder.toTeam
            for player in self.players:
                if player.session is None or player.team != toTeam:
                    continue
                player.session.sendXml(builder)
        else:
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

    def addUser(self, session: Session, roomCreate: bool = False):
        assert self.server.mode == "ANY" or session.serverMode == self.serverMode

        builder = XMLBuilder("ENTER")

        bRoom = builder.room
        for user_ in self.users:
            bUser = bRoom.user
            bUser.name(user_.userName)
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
                player.writeXML(bPlayers.player)

        if self.playing:
            privPlayer = self.getPlayer(session.userName)
            if privPlayer is not None:
                bGame.dealCount(str(privPlayer.deal))
                bPrivPlayer = bGame.privatePlayer
                bPrivPlayer.time("1475196662616")
                for piece in privPlayer.pieces:
                    bPrivPlayer.item.item(str(piece.getItemOrIllusion().id))
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
                for piece in atkData.pieceList:
                    piece.writeXML(bCommand.piece)
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
                if atkData.attacker == atkData.defender and atkData.decidedPiece is not None:
                    atkData.decidedPiece.writeXML(builder.commandChain.piece)

        session.sendXml(builder)

        session.state = "ROOM"
        self.users.append(session)

        builder = XMLBuilder("ADD_USER")
        builder.user.name(session.userName)
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

    def removeUser(self, session: Session):
        if session not in self.users:
            return

        self.users.remove(session)

        if len(self.users) == 0:
            # Destroy Room
            del self.server.rooms[self.id]
        else:
            builder = XMLBuilder("REMOVE_USER")
            builder.name(session.userName)
            self.broadXml(builder)

        # Broadcast to Lobby
        builder = XMLBuilder("REMOVE_USER")
        builder.roomID(str(self.id))
        builder.user.name(session.userName)
        self.server.lobbyBroadXml(builder)

    def enterGame(self, session: Session, team: str):
        assert team in ["SINGLE"] + Room.VALID_TEAMS
        if self.playing:
            return

        player = self.getPlayer(session.userName)

        if len(self.players) == 0:
            self.teamPlay = team != "SINGLE"
        else:
            assert self.teamPlay == (team != "SINGLE"), "Player tried to choose an impossible team"

        if player is None:
            player = Player(self, session, team)
            self.players.append(player)
        else:
            player.team = team

        print(f"Add player: {session.userName}@{team}")

        builder = XMLBuilder("ADD_PLAYER")
        bPlayer = builder.player
        bPlayer.name(player.name)
        bPlayer.team(player.team)
        self.broadXml(builder)

        # Reuse builder to broadcast to lobby
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
                    self.turn.attackerCommand(player, *player.aiProcessor.onAttackTurn())
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

            # Reuse builder to broadcast to lobby
            builder.roomID(str(self.id))
            self.server.lobbyBroadXml(builder)

    def shuffleTeam(self):
        if self.playing or not self.teamPlay:
            return
        if len(self.players) in [0, 1, 2, 3, 5, 7]:
            return

        # To be honest, I don't know how this should be implemented, the below implementation is just a guess.
        # TODO: Improve this.
        players = list(self.players)
        random.shuffle(players)

        for idx, player in enumerate(players):
            assert player.session is not None
            if idx < len(self.players) / 2:
                self.enterGame(player.session, Room.VALID_TEAMS[0])
            else:
                self.enterGame(player.session, Room.VALID_TEAMS[1])

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

        # Reuse builder to broadcast to lobby
        builder.roomID(str(self.id))
        builder.time(str(self.time))
        self.server.lobbyBroadXml(builder)

        self.nextInning()

    def endGame(self):
        self.playing = False
        self.ended = True

        for player in self.players:
            if "ILLUSION" in player.harms:
                player.unillusionPieces()

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

            if self.getAliveCount() >= 2 and (piece := player.getOwnedPieceById(244)) is not None:  # REVIVE
                self.turn.playerDyingAttack(player, piece)
                continue

            player.dead = True

            builder = XMLBuilder("DIE")
            builder.player.name(player.name)
            self.broadXml(builder)

            if self.getAliveCount() >= 2 and (piece := player.getOwnedPieceById(117)) is not None:  # DYING_ATTACK
                self.turn.playerDyingAttack(player, piece)
            else:
                # TODO: Check if it makes sense to unillusion/unfog even if we will be doing a dying attack.
                if "ILLUSION" in player.harms:
                    player.pendingUnillusion = True
                if "FOG" in player.harms:
                    player.pendingUnfog = True

                if player.team == "SINGLE":
                    player.lost = True
                elif player.team not in self.getAliveTeams():
                    for _player in self.players:
                        if _player.team == player.team:
                            _player.lost = True

                # Reuse builder to broadcast to lobby
                builder.roomID(str(self.id))
                self.server.lobbyBroadXml(builder)

    def handlePlayersUnillusion(self):
        for player in self.players:
            if player.pendingUnillusion:
                player.unillusionPieces()

    def handlePlayersUnfog(self):
        for player in self.players:
            if player.pendingUnfog:
                player.unfog()

    def doPlayersDeals(self):
        for player in self.players:
            print(player.name, "HP:", player.hp, "MP:", player.mp, "YEN:", player.yen, "PIECES:", len(player.pieces), "MAGICS:", len(player.magics), "DISEASE:", player.disease if player.disease else "None", "HARMS:", player.harms)
            if player.deal > 0 and not player.dead:
                if player.session is not None or self.fdIncludeBots:
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
        self.handlePlayersUnillusion()
        self.handlePlayersUnfog()

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
                if player.dead or player.assistant is None or not player.isEnemy(self.turn.attacker):
                    continue
                if random.randrange(100) < 30:
                    player.assistant.onAttackOpportunity()

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
        while True:
            if not self.endInning():
                # Player input is required to proceed.
                break

            if self.checkEndGame():
                self.endGame()
                return

            self.startInning()

            if self.turn.attacker.aiProcessor is not None:
                self.turn.attackerCommand(self.turn.attacker, *self.turn.attacker.aiProcessor.onAttackTurn())
                continue

            # Player input is required to proceed.
            break


