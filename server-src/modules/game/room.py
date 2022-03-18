# -*- coding: cp1252 -*-
from helpers.xmlbuilder import XMLBuilder
from modules.game.player import Player
from modules.game.bot import Bot
from modules.game.turn import TurnHandler

import random


class Room:
    def __init__(self, server, name, password=""):
        self.server = server

        self.id = int()
        self.name = name
        self.password = password
        self.language = str()
        self.playersLimit = int()
        self.time = int()
        self.fast = bool()
        self.playing = bool()
        self.inningCount = int()
        self.attackOrderList = list()
        self.attackOrder = -1
        self.ended = bool()

        self.teamPlay = bool()

        self.turn = TurnHandler(self)

        self.forceNextDeal = None

        self.users = list()
        self.players = list()

    def broadXml(self, xml):
        for user in self.users:
            user.sendXml(xml)

    def getPlayer(self, name):
        for player in self.players:
            if player.name == name:
                return player
        return None

    def sendChat(self, sender, msg):
        builder = XMLBuilder("CHAT")
        builder.name(sender)
        builder.comment(msg)
        self.broadXml(builder)

    def addUser(self, user, roomCreate = False):
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
                if player.disease is not None:
                    bPlayer.disease(player.disease)
                for harm in player.harms:
                    bPlayer.harm(harm)
                # TODO: Assistant
        # TODO: privatePlayer (regain control after disconnect)
        if self.playing:
            bAttacker = bGame.attacker
            if self.turn.currentAttack is None:
                bAttacker.name(str(self.turn.attacker.name))
            else:
                atkData = self.turn.currentAttack

                # TODO: retargeted attacks appears as normal attacks... idk if there's any way to fix this
                bAttacker.name(str(atkData.attacker.name))
                bCommand = bGame.COMMAND
                for item in atkData.piece:
                    pp = bCommand.piece
                    pp.item(str(item.id))
                    if item.attackExtra == "MAGICAL":
                        pp.costMP(str(atkData.damage / 2))
                if atkData.decidedValue is not None:
                    bCommand.decidedValue(str(atkData.decidedValue))
                bCommand.commander.name(atkData.attacker.name)
                if not atkData.isAction:
                    bCommand.target.name(atkData.defender.name)

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

    def removeUser(self, user):
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

    def enterGame(self, user, team):
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

        print "Add player:", user.name + "@" + team

        builder = XMLBuilder("ADD_PLAYER")
        bPlayer = builder.player
        bPlayer.name(player.name)
        bPlayer.team(player.team)
        self.broadXml(builder)

        # Broadcast to Lobby
        builder.roomID(str(self.id))
        self.server.lobbyBroadXml(builder)

        return player

    def exitGame(self, player):
        if player not in self.players:
            return

        print "Remove player:", player.name

        if self.playing:
            bot = Bot(player.name, player.team)
            bot.server = self.server
            bot.room = self
            bot.setFromPlayer(player)
            self.players[self.players.index(player)] = bot
            if player in self.attackOrderList:
                self.attackOrderList[self.attackOrderList.index(player)] = bot

            endInning = None
            atkData = self.turn.currentAttack
            if atkData is None:
                if self.turn.attacker == player:
                    self.turn.attacker = bot
                    self.turn.newAttack(bot, *bot.on_turn())
                    endInning = True
            elif atkData.defender == player:
                atkData.defender = bot
                endInning = self.turn.defenderCommand(bot, bot.on_attack())
            
            if endInning is not None:
                while endInning:
                    endInning = self.endInning()
        else:
            self.players.remove(player)

            builder = XMLBuilder("REMOVE_PLAYER")
            builder.player.name(player.name)
            self.broadXml(builder)

            builder.roomID(str(self.id))
            self.server.lobbyBroadXml(builder)

    def playerReady(self, playerName):
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
        assert len(self.players)>0, "StartGame called without players."
        
        self.inningCount = -1
        self.playing = True
        self.ended = False
        for player in self.players:
            player.reset()
            player.ready = True

        self.attackOrder = -1

        builder = XMLBuilder("START_GAME")
        self.broadXml(builder)
        
        builder.roomID(str(self.id))
        builder.time(str(self.time))
        self.server.lobbyBroadXml(builder)

        while self.endInning(self.turn.attacker is not None):
            pass

    def getAlivesCount(self):
        count = 0
        for player in self.players:
            if not player.dead:
                count += 1
        return count

    def getEnemiesAliveCount(self, team):
        count = 0
        for player in self.players:
            if not player.dead and player.team != team:
                count += 1
        return count

    def getAliveTeams(self):
        aliveTeams = []
        for player in self.players:
            if not player.dead and player.team not in aliveTeams:
                aliveTeams.append(player.team)
        return aliveTeams

    def getTeamsAliveCount(self):
        return len(self.getAliveTeams())

    def checkEndGame(self):
        if self.teamPlay:
            if self.getTeamsAliveCount() <= 1:
                self.ended = True

        elif self.getAlivesCount() <= 1:
            self.ended = True

        if self.ended:
            builder = XMLBuilder("END_GAME")
            self.broadXml(builder)

            return True

        return False

    def handlePlayersDeath(self):
        for player in self.players:
            if player.hp > 0 or player.dead:
                continue
            
            if self.getAlivesCount() >= 2 and player.hasItem(244):  # REVIVE
                self.turn.playerDyingAttack(player, self.server.itemManager.getItem(244))
            elif self.getAlivesCount() >= 2 and player.hasItem(117):  # DYING_ATTACK
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
            print player.name, "HP:", player.hp, "MP:", player.mp, "YEN:", player.yen, "ITEMS:", len(player.items)
            if player.deal > 0 and not player.dead:
                if player.deal == 10:
                    items = self.server.itemManager.getProbRandomItems(7)  # 10
                    for item in items:
                        player.dealItem(item.id)
                #    player.dealItem(220)
                #    player.dealItem(221)
                #    player.dealItem(237)
                #    player.dealItem(243)
                #    player.dealItem(39) #244
                #    #player.dealItem(20)
                #    #player.dealItem(233)
                #    #player.dealItem(39)
                #    player.dealItem(63)
                #    player.dealItem(233)
                #    player.dealItem(234)  # Heaven Herb
                #    player.dealItem(242)
                #    player.dealItem(244) #212 = Arco da morte, 244 = Reviver
                #    player.dealItem(191) #194 = Take Yen, 188 = FOG, 191 = Glory ring
                    player.dealItem(3)
                    player.dealItem(2)
                    player.dealItem(2)
                else:
                    if self.forceNextDeal is None:
                        items = self.server.itemManager.getProbRandomItems(player.deal)
                        for item in items:
                            player.dealItem(item.id)
                    else:
                        player.dealItem(self.forceNextDeal)
                player.deal = 0

        if self.forceNextDeal is not None:
            self.forceNextDeal = None

    def resetAttackOrder(self):
        self.attackOrderList = list(self.players)
        random.shuffle(self.attackOrderList)

        for player in self.players:
            player.waitingAttackTurn = True
        
        builder = XMLBuilder("RESET_ATTACK_ORDER")
        self.broadXml(builder)

    def nextInning(self):
        self.attackOrder = (self.attackOrder + 1) % len(self.players)
        if self.attackOrder == 0:
            self.resetAttackOrder()
        
        next = self.attackOrderList[self.attackOrder]
        while next.dead:
            self.attackOrder = (self.attackOrder + 1) % len(self.players)
            next = self.attackOrderList[self.attackOrder]

        return self.startInning(next)

    def startInning(self, attacker):
        assert(attacker in self.players)

        self.turn.new()
        self.turn.attacker = attacker
        self.turn.attacker.waitingAttackTurn = False

        self.inningCount += 1
        
        builder = XMLBuilder("START_INNING")
        builder.attacker.name(attacker.name)
        self.broadXml(builder)

        if isinstance(attacker, Bot):
            self.turn.newAttack(attacker, *attacker.on_turn())
            return True

    def endInning(self, applyDiseaseEffect = True):
        self.handlePlayersDeath()

        if not self.turn.attackQueue.empty():
            return self.turn.doAttack()
        
        if applyDiseaseEffect and not self.turn.attacker.dead and self.turn.attacker.disease is not None:
            gotWorse = False
            if random.random() * 100 < self.turn.attacker.worseChance:
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
                    return self.endInning(False)

        print "Round", self.inningCount+1, "ended, starting new round.."

        self.doPlayersDeals()
        
        builder = XMLBuilder("END_INNING")
        self.broadXml(builder)

        if not self.checkEndGame():
            return self.nextInning()
        
        # Game has ended
        return False


