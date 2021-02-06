from modules.game.bot import Bot
from helpers.xmlbuilder import XMLBuilder


class Session:
    def __init__(self, user,  xmldict):
        self.name = xmldict["name"]
        self.ipAddress = xmldict["ipAddress"] if "ipAddress" in xmldict else ""
        self.language = xmldict["language"]
        self.oneTimeID = xmldict["oneTimeID"]
        self.state = "UNKNOWN"
        self.handlers = dict()

        self.user = user
        self.server = user.server
        self.room = None
        self.player = None

    def registerHandlers(self):
        self.handlers["ENTER"] = self.enterHandler
        self.handlers["EXIT"] = self.exitHandler
        self.handlers["CHAT"] = self.chatHandler
        self.handlers["ENTER_GAME"] = self.enterGameHandler
        self.handlers["EXIT_GAME"] = self.exitGameHandler
        self.handlers["READY"] = self.readyHandler
        self.handlers["BUY"] = self.buyHandler
        self.handlers["COMMAND"] = self.commandHandler

    def sendXml(self, xml):
        self.user.sendXml(xml)

    def gotoLobby(self):
        self.sendXml(self.server.buildLobbyXml())
        self.state = "LOBBY"

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
        self.registerHandlers()

        if self.server.mode == "FREEFIGHT":
            self.gotoLobby()
            self.server.addUser(self)
        else:
            raise Exception("Unsupported server mode")
        #    self.transport.write("""<?xml version="1.0" encoding="UTF-8" standalone="no"?><ENTER><room><game><players><player><name>Igoor</name><team>SINGLE</team><isReady/><power key="HP">90</power><power key="MP">90</power><power key="YEN">90</power></player><player><name>Sinbad</name><team>SINGLE</team><isReady/><power key="HP">40</power><power key="MP">10</power><power key="YEN">20</power></player><player><name>Santa Claus</name><team>SINGLE</team><isReady/><power key="HP">40</power><power key="MP">10</power><power key="YEN">20</power></player><player><name>Odin</name><team>SINGLE</team><isReady/><power key="HP">40</power><power key="MP">10</power><power key="YEN">20</power></player></players><privatePlayer/></game></room></ENTER>""" + chr(0))
        #    self.transport.write("""<?xml version="1.0" encoding="UTF-8" standalone="no"?><ADD_USER><user><name>Igoor</name></user></ADD_USER><?xml version="1.0" encoding="UTF-8" standalone="no"?><START_GAME/><?xml version="1.0" encoding="UTF-8" standalone="no"?><RESET_ATTACK_ORDER/><?xml version="1.0" encoding="UTF-8" standalone="no"?><DEAL><item>220</item></DEAL><?xml version="1.0" encoding="UTF-8" standalone="no"?><DEAL><item>190</item></DEAL><?xml version="1.0" encoding="UTF-8" standalone="no"?><DEAL><item>150</item></DEAL><?xml version="1.0" encoding="UTF-8" standalone="no"?><DEAL><item>126</item></DEAL><?xml version="1.0" encoding="UTF-8" standalone="no"?><DEAL><item>104</item></DEAL><?xml version="1.0" encoding="UTF-8" standalone="no"?><DEAL><item>4</item></DEAL><?xml version="1.0" encoding="UTF-8" standalone="no"?><DEAL><item>77</item></DEAL><?xml version="1.0" encoding="UTF-8" standalone="no"?><DEAL><item>187</item></DEAL><?xml version="1.0" encoding="UTF-8" standalone="no"?><DEAL><item>72</item></DEAL><?xml version="1.0" encoding="UTF-8" standalone="no"?><DEAL><item>41</item></DEAL><?xml version="1.0" encoding="UTF-8" standalone="no"?><END_INNING/><?xml version="1.0" encoding="UTF-8" standalone="no"?><START_INNING><attacker><name>Sinbad</name></attacker></START_INNING><?xml version="1.0" encoding="UTF-8" standalone="no"?><COMMAND><piece><item>48</item></piece><piece><item>44</item></piece><commander><name>Sinbad</name></commander><target><name>Santa Claus</name></target></COMMAND><?xml version="1.0" encoding="UTF-8" standalone="no"?><COMMAND><piece><item>19</item></piece><piece><item>11</item></piece></COMMAND><?xml version="1.0" encoding="UTF-8" standalone="no"?><END_INNING/><?xml version="1.0" encoding="UTF-8" standalone="no"?><START_INNING><attacker><name>Igoor</name></attacker></START_INNING>""".replace("<?xml", "\0<?xml") + chr(0))

    def onRequest(self, request, xmldict):
        if request != "ENTER" and self.room is None:
            return

        handler = self.handlers.get(request)
        if handler is not None:
            handler(xmldict)
            
    def enterHandler(self, xmldict):
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

    def exitHandler(self, xmldict):
        self.room.removeUser(self)
        if self.player is not None:
            self.room.exitGame(self.player)

        self.room = None
        self.player = None

        self.gotoLobby()

    def chatHandler(self, xmldict):
        comment = xmldict.get("comment")
        if comment is None or len(comment.strip()) == 0:
            return

        args = comment.split(" ")[1:]

        if comment == "go":
            self.room.startGame()
        elif comment == "die":
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
        elif comment.startswith("newbot") and not self.room.playing:
            count = int(args[0]) if len(args) > 0 else 1
            team = args[1].upper() if len(args) > 1 else "SINGLE"
            if len(self.room.players) == 0: # TODO: Move this to room class
                self.room.teamPlay = team != "SINGLE"
            for i in range(count):
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

    def enterGameHandler(self, xmldict):
        team = xmldict.get("team")
        if team is not None:
            self.player = self.room.enterGame(self, team)

    def exitGameHandler(self, xmldict):
        self.room.exitGame(self.player)
        self.player = None

    def readyHandler(self, xmldict):
        self.player.ready = "isReady" in xmldict
        self.room.playerReady(self.player.name)

    def buyHandler(self, xmldict):
        response = "doBuy" in xmldict
        self.room.turn.playerBuyResponse(self.player, response)

        while self.room.endInning():
            pass

    def commandHandler(self, xmldict):
        piece = xmldict.get("piece", [])
        target = xmldict.get("@target")

        if type(piece) is not list:
            piece = [piece]

        endInning = False

        # Convert ids to instances
        piece = map(lambda x: self.server.itemManager.getItem(int(x.values()[0])), piece)

        if target is not None:
            endInning = self.room.turn.attackerCommand(self.player, piece, self.room.getPlayer(target))
        else:
            endInning = self.room.turn.defenderCommand(self.player, piece)

        while endInning:
            endInning = self.room.endInning()

        #self.transport.write("""<?xml version="1.0" encoding="UTF-8" standalone="no"?><COMMAND><piece><item>88</item></piece><commander><name>Igoor</name></commander><target><name>Odin</name></target></COMMAND>""" + chr(0))
        #self.transport.write("""<?xml version="1.0" encoding="UTF-8" standalone="no"?><COMMAND/><?xml version="1.0" encoding="UTF-8" standalone="no"?><COMMAND><piece><item>200</item></piece><isMiss/><commander><name>Igoor</name></commander><target><name>Robin Hood</name></target></COMMAND><?xml version="1.0" encoding="UTF-8" standalone="no"?><COMMAND><piece><item>200</item></piece><isMiss/><commander><name>Igoor</name></commander><target><name>Santa Claus</name></target></COMMAND><?xml version="1.0" encoding="UTF-8" standalone="no"?><DEAL><item>22</item></DEAL><?xml version="1.0" encoding="UTF-8" standalone="no"?><END_INNING/><?xml version="1.0" encoding="UTF-8" standalone="no"?><RESET_ATTACK_ORDER/><?xml version="1.0" encoding="UTF-8" standalone="no"?><START_INNING><attacker><name>Igoor</name></attacker></START_INNING>""".replace("<?xml", "\0<?xml") + chr(0))