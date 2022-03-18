from __future__ import annotations
from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from server import Server
    from modules.user import User
    from modules.room import Room
from modules.player import Player
from modules.bot import Bot
from helpers.xmlbuilder import XMLBuilder

import random

__all__ = ("Session",)


handlers = dict()
def request(name):
    def wrapper(func):
        handlers[name] = func
        return func
    return wrapper

class Session:
    name: str
    ipAddress: str
    language: str
    oneTimeID: str
    state: str
    user: User
    server: Server
    room: Optional[Room]
    player: Optional[Player]

    __slots__ = tuple(__annotations__)

    def __init__(self, user: User,  xmldict):
        self.name = xmldict["name"]
        self.ipAddress = xmldict["ipAddress"] if "ipAddress" in xmldict else ""
        self.language = xmldict["language"]
        self.oneTimeID = xmldict["oneTimeID"]
        self.state = "UNKNOWN"

        self.user = user
        self.server = user.server
        self.room = None
        self.player = None

    def sendXml(self, xml):
        self.user.sendXml(xml)

    def onDisconnect(self):
        self.server.removeUser(self)
        self.state = "DISCONNECTED"
        
        if self.room is not None:
            if self.player is not None:
                self.room.exitGame(self.player)
                self.player = None
            self.room.removeUser(self)
            self.room = None

    def onLogin(self):
        serverMode = self.user.getServerMode()
        if serverMode == "TRAINING":
            self.gotoTraining()
            self.server.addUser(self)
        elif serverMode == "FREE_FIGHT":
            self.gotoLobby()
            self.server.addUser(self)
        else:
            raise Exception("Unsupported server mode")

    def gotoLobby(self):
        self.sendXml(self.server.buildLobbyXml())
        self.state = "LOBBY"

    def gotoTraining(self):
        self.room = self.server.createRoom("", "".join(__import__("random").choice(__import__("string").ascii_uppercase + __import__("string").digits) for _ in range(12)))
        self.room.language = self.language
        self.room.playersLimit = 4
        self.room.time = 1475196662616

        self.player = Player(self, self.name, "SINGLE")
        self.player.ready = True
        self.room.players.append(self.player)

        botNames = ["Princess Kaguya", "Sinbad", "Odin", "Santa Claus", "Robin Hood"]
        for _ in range(3):
            b = Bot(random.choice(botNames), "SINGLE")
            b.server = self.server
            b.room = self.room
            b.ready = True
            self.room.players.append(b)

        self.room.addUser(self)
        self.room.startGame()
        
    def onRequest(self, request, xmldict):
        if request != "ENTER" and self.room is None:
            return
        
        handler = handlers.get(request)
        if handler is not None:
            handler(self, xmldict)
    
    @request("ENTER")
    def enterHandler(self, xmldict):
        assert self.room is None

        roomName = xmldict.get("name")
        roomId = xmldict.get("id")
        room = None

        if roomName is not None:
            room = self.server.createRoom(roomName)
            room.language = self.language
            room.playersLimit = int(xmldict.get("playersLimit", 2))
            room.fast = "isFast" in xmldict
            room.time = 1475196662616
        elif roomId is not None:
            room = self.server.getRoom(int(roomId))

        if room is not None:
            self.room = room
            self.room.addUser(self, roomName is not None)

    @request("EXIT")
    def exitHandler(self, xmldict):
        assert self.room is not None

        self.room.removeUser(self)
        if self.player is not None:
            self.room.exitGame(self.player)

        self.room = None
        self.player = None

        self.gotoLobby()

    @request("CHAT")
    def chatHandler(self, xmldict):
        assert self.room is not None

        comment = xmldict.get("comment")
        if comment is None or len(comment.strip()) == 0:
            return

        args = comment.split(" ")[1:]

        if comment == "go":
            self.room.startGame()

        elif comment == "test_go":
            for _ in range(100):
                self.room.startGame()

        elif comment == "die":
            if self.player is not None:
                self.player.hp = 0

        elif comment.startswith("kill"):
            for player in self.room.players:
                if player == self.player or player.dead:
                    continue
                player.hp = 0
                if len(args) == 0 or args[0] != "all":
                    break

        elif comment == "sdie":
            builder = XMLBuilder("DIE")
            builder.player.name(self.name)
            self.sendXml(builder)

        elif comment.startswith("fnd") and len(args) > 0:
            self.room.forceNextDeal = int(args[0])

        elif comment.startswith("fid"):
            self.room.forceInitialDeal = list(map(int, args[0].split("+"))) if len(args) > 0 else None

        elif comment.startswith("newbot") and not self.room.playing:
            count = int(args[0]) if len(args) > 0 else 1
            team = args[1].upper() if len(args) > 1 else "SINGLE"
            if len(self.room.players) == 0: # TODO: Move this to room class
                self.room.teamPlay = team != "SINGLE"
            for _ in range(count):
                b = Bot(''.join(__import__("random").choice(__import__("string").ascii_uppercase + __import__("string").digits) for _ in range(12)), team)
                b.server = self.server
                self.room.players.append(b)
                b.room = self.room
                b.ready = True

                # TODO: Move this to room class
                builder = XMLBuilder("ADD_PLAYER")
                bPlayer = builder.player
                bPlayer.name(b.name)
                bPlayer.team(b.team)
                self.room.broadXml(builder)

                # Set as ready (It needs to be a separate xml)
                builder = XMLBuilder("ADD_PLAYER")
                bPlayer = builder.player
                bPlayer.name(b.name)
                bPlayer.isReady
                self.room.broadXml(builder)

                # Broadcast to Lobby
                builder.roomID(str(self.room.id))
                self.server.lobbyBroadXml(builder)

        self.room.sendChat(self.name, comment)

    @request("ENTER_GAME")
    def enterGameHandler(self, xmldict):
        assert self.room is not None

        team = xmldict.get("team")
        if team is not None:
            self.player = self.room.enterGame(self, team)

    @request("EXIT_GAME")
    def exitGameHandler(self, xmldict):
        assert self.room is not None
        assert self.player is not None

        self.room.exitGame(self.player)
        self.player = None

    @request("READY")
    def readyHandler(self, xmldict):
        assert self.room is not None
        assert self.player is not None

        self.player.ready = "isReady" in xmldict
        self.room.playerReady(self.player.name)

    @request("BUY")
    def buyHandler(self, xmldict):
        assert self.room is not None
        assert self.player is not None

        response = "doBuy" in xmldict
        self.room.turn.playerBuyResponse(self.player, response)

        self.room.nextInning()

    @request("COMMAND")
    def commandHandler(self, xmldict):
        assert self.room is not None
        assert self.player is not None

        piece = xmldict.get("piece", [])
        target = xmldict.get("@target")
        power = xmldict.get("power", None)

        if type(piece) is not list:
            piece = [piece]

        # Convert ids to instances
        piece = [self.server.itemManager.getItem(int(list(x.values())[0])) for x in piece]
        
        decidedExchange = None
        if power is not None:
            decidedExchange = dict()
            for kv in power:
                key = kv.get("@key")
                value = int(kv.get("#text"))
                decidedExchange[key] = value

        endInning = False
        if target is not None:
            target = self.room.getPlayer(target)
            assert target is not None
            endInning = self.room.turn.attackerCommand(self.player, piece, target, decidedExchange)
        else:
            endInning = self.room.turn.defenderCommand(self.player, piece)

        if endInning:
            self.room.nextInning()