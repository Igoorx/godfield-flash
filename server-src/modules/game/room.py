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
        self.ended = False

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

    def addUser(self, user):
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
            bPlayers = bGame.players
            for player in self.players:
                bPlayer = bPlayers.player
                bPlayer.name(player.name)
                bPlayer.team(player.team)
                if player.ready:
                    bPlayer.isReady  # <isReady />
                if self.playing and player.dead:
                    bPlayer.isDead  # <isDead />
                bPlayer.power(key="HP")(str(player.hp))
                bPlayer.power(key="MP")(str(player.mp))
                bPlayer.power(key="YEN")(str(player.yen))
        user.sendXml(builder)

        user.state = "ROOM"
        self.users.append(user)

        builder = XMLBuilder("ADD_USER")
        builder.user.name(user.name)
        self.broadXml(builder)

        # Broadcast to Lobby
        bRoom = builder.room
        bRoom.name(self.name)
        bRoom.id(str(self.id))
        bRoom.language(self.language)
        bRoom.playersLimit(str(self.playersLimit))
        if self.fast:
            bRoom.isFast(str(self.fast))
        bRoom.time(str(self.time))
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

        if player is None:
            player = Player(user, user.name, team)
            self.players.append(player)
        else:
            player.team = team

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

        #TODO: Ver como o server original trata qnd um player sai durante uma partida 1x1

        self.players.remove(player)
        if player in self.attackOrderList:
            self.attackOrderList.remove(player)

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
        for player in self.players:
            player.dead = False
            player.deal = 10
            player.hp = 40
            player.mp = 10
            player.yen = 20
            player.resetItems()

        self.attackOrder = -1

        builder = XMLBuilder("START_GAME")
        self.broadXml(builder)

        while self.endInning():
            pass

    def getAlivesCount(self):
        count = 0
        for player in self.players:
            if not player.dead:
                count += 1
        return count

    def nextInning(self):
        self.attackOrder = (self.attackOrder+1)%len(self.players)
        if self.attackOrder == 0:
            self.attackOrderList = list(self.players)
            random.shuffle(self.attackOrderList)
            
            builder = XMLBuilder("RESET_ATTACK_ORDER")
            self.broadXml(builder)
        
        next = self.attackOrderList[self.attackOrder]
        while next.dead:
            self.attackOrder = (self.attackOrder+1)%len(self.players)
            next = self.attackOrderList[self.attackOrder]

        return self.startInning(next)

    def startInning(self, attacker):
        self.turn.new()
        self.turn.attacker = attacker

        self.inningCount += 1
        
        builder = XMLBuilder("START_INNING")
        builder.attacker.name(attacker.name)
        self.broadXml(builder)

        if isinstance(attacker, Bot):
            self.turn.newAttack(attacker, *attacker.on_turn())
            return self.turn.doAttack()

    def endInning(self):
        for player in self.players:
            if player.hp <= 0 and not player.dead:
                if self.getAlivesCount() >= 2 and player.hasItem(244):  # REVIVE
                    self.turn.playerDyingAttack(player, self.server.itemManager.getItem(244))
                elif self.getAlivesCount() >= 2 and player.hasItem(117):  # DYING_ATTACK
                    self.turn.playerDyingAttack(player, self.server.itemManager.getItem(117))
                else:
                    player.dead = True
                    builder = XMLBuilder("DIE")
                    builder.player.name(player.name)
                    self.broadXml(builder)

        if not self.turn.attackQueue.empty():
            return self.turn.doAttack()

        print "Round", self.inningCount+1, "ended, starting new round.."

        for player in self.players:
            print player.name, "HP:", player.hp, "MP:", player.mp, "YEN:", player.yen
            if player.deal > 0 and not player.dead:
                if player.deal == 10:
                    items = self.server.itemManager.getProbRandomItems(9)  # 10
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
                #    player.dealItem(242)
                #    player.dealItem(244) #212 = Arco da morte, 244 = Reviver
                #    player.dealItem(191) #194 = Take Yen, 188 = FOG, 191 = Glory ring
                    player.dealItem(190)
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
        
        builder = XMLBuilder("END_INNING")
        self.broadXml(builder)

        if self.getAlivesCount() <= 1:
            self.ended = True
            builder = XMLBuilder("END_GAME")
            self.broadXml(builder)
            return False
        else:
            return self.nextInning()


