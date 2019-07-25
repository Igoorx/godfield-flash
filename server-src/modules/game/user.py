from twisted.internet import reactor, protocol

from helpers.xmltodict import parse as xmltodict
from helpers.xmlbuilder import XMLBuilder


class User(protocol.Protocol):
    def __init__(self):
        self.recvd = str()

        self.name = str()
        self.ipAddress = str()
        self.language = str()
        self.oneTimeID = str()
        self.state = "UNKNOWN"

        self.server = None
        self.room = None
        self.player = None

    def connectionMade(self):
        self.server = self.factory

    def connectionLost(self, reason):
        if self.state != "UNKNOWN":
            self.server.users.remove(self)

            builder = XMLBuilder("REMOVE_USER")
            builder.user.name(self.name)
            self.server.lobbyBroadXml(builder)

        if self.room is not None:
            if self.player is not None:
                self.room.exitGame(self.player)
            self.room.removeUser(self)
    
    def dataReceived(self, data):
        if data == "<policy-file-request/>\0":
            self.transport.write("<cross-domain-policy><allow-access-from domain=\"*\" to-ports=\"*\" /></cross-domain-policy>\0")
            self.transport.loseConnection()
            return

        self.recvd += data

        if not data.endswith("\0"):
            return

        xmls = self.recvd.split("\0")
        for xml in xmls:
            if xml == str(): break
            xml = xml.replace("\n", " ")
            
            self.parseXml(xml)

        self.recvd = str()

    def sendXml(self, xml):
        print "SEND ("+self.name+"):", repr(str(xml))
        self.transport.write(str(xml) + chr(0))

    def parseXml(self, xml):
        xmldict = xmltodict(xml)
        request = xmldict.keys()[0]
        xmldict = xmldict.values()[0] if xmldict.values()[0] != None else dict()

        #print repr(xml)
        #print "RECV ("+self.name+"):", request, xmldict

        #<player><name>Igoor</name><team>SINGLE</team><isReady/><power key="HP">90</power><power key="MP">90</power><power key="YEN">90</power></player><player><name>Sinbad</name><team>SINGLE</team><isReady/><power key="HP">40</power><power key="MP">10</power><power key="YEN">20</power></player><player><name>Santa Claus</name><team>SINGLE</team><isReady/><power key="HP">40</power><power key="MP">10</power><power key="YEN">20</power></player><player><name>Odin</name><team>SINGLE</team><isReady/><power key="HP">40</power><power key="MP">10</power><power key="YEN">20</power></player></players><privatePlayer/></game></room></ENTER>""" + chr(0))

        if request == "ERROR":
            print request, xmldict

        if request == "LOGIN":
            self.name = xmldict["name"]
            self.ipAddress = xmldict["ipAddress"]
            self.language = xmldict["language"]
            self.oneTimeID = xmldict["oneTimeID"]

            if self.server.getUser(self.name):
                self.transport.loseConnection()
                return

            if self.server.mode == "FREEFIGHT":
                self.server.gotoLobby(self)
                self.server.users.append(self)

                builder = XMLBuilder("ADD_USER")
                builder.user.name(self.name)
                for user in self.server.users:
                    if user.state != "LOBBY":
                        continue
                    user.sendXml(builder)
            else:
                self.transport.write("""<?xml version="1.0" encoding="UTF-8" standalone="no"?><ENTER><room><game><players><player><name>Igoor</name><team>SINGLE</team><isReady/><power key="HP">90</power><power key="MP">90</power><power key="YEN">90</power></player><player><name>Sinbad</name><team>SINGLE</team><isReady/><power key="HP">40</power><power key="MP">10</power><power key="YEN">20</power></player><player><name>Santa Claus</name><team>SINGLE</team><isReady/><power key="HP">40</power><power key="MP">10</power><power key="YEN">20</power></player><player><name>Odin</name><team>SINGLE</team><isReady/><power key="HP">40</power><power key="MP">10</power><power key="YEN">20</power></player></players><privatePlayer/></game></room></ENTER>""" + chr(0))
                self.transport.write("""<?xml version="1.0" encoding="UTF-8" standalone="no"?><ADD_USER><user><name>Igoor</name></user></ADD_USER><?xml version="1.0" encoding="UTF-8" standalone="no"?><START_GAME/><?xml version="1.0" encoding="UTF-8" standalone="no"?><RESET_ATTACK_ORDER/><?xml version="1.0" encoding="UTF-8" standalone="no"?><DEAL><item>220</item></DEAL><?xml version="1.0" encoding="UTF-8" standalone="no"?><DEAL><item>190</item></DEAL><?xml version="1.0" encoding="UTF-8" standalone="no"?><DEAL><item>150</item></DEAL><?xml version="1.0" encoding="UTF-8" standalone="no"?><DEAL><item>126</item></DEAL><?xml version="1.0" encoding="UTF-8" standalone="no"?><DEAL><item>104</item></DEAL><?xml version="1.0" encoding="UTF-8" standalone="no"?><DEAL><item>4</item></DEAL><?xml version="1.0" encoding="UTF-8" standalone="no"?><DEAL><item>77</item></DEAL><?xml version="1.0" encoding="UTF-8" standalone="no"?><DEAL><item>187</item></DEAL><?xml version="1.0" encoding="UTF-8" standalone="no"?><DEAL><item>72</item></DEAL><?xml version="1.0" encoding="UTF-8" standalone="no"?><DEAL><item>41</item></DEAL><?xml version="1.0" encoding="UTF-8" standalone="no"?><END_INNING/><?xml version="1.0" encoding="UTF-8" standalone="no"?><START_INNING><attacker><name>Sinbad</name></attacker></START_INNING><?xml version="1.0" encoding="UTF-8" standalone="no"?><COMMAND><piece><item>48</item></piece><piece><item>44</item></piece><commander><name>Sinbad</name></commander><target><name>Santa Claus</name></target></COMMAND><?xml version="1.0" encoding="UTF-8" standalone="no"?><COMMAND><piece><item>19</item></piece><piece><item>11</item></piece></COMMAND><?xml version="1.0" encoding="UTF-8" standalone="no"?><END_INNING/><?xml version="1.0" encoding="UTF-8" standalone="no"?><START_INNING><attacker><name>Igoor</name></attacker></START_INNING>""".replace("<?xml", "\0<?xml") + chr(0))

        if request == "ENTER":
            if "name" in xmldict:
                room = self.server.createRoom(xmldict["name"])
                room.language = self.language
                room.playersLimit = int(xmldict["playersLimit"])
                room.fast = "isFast" in xmldict
                room.time = 1475196662616
            elif "id" in xmldict:
                room = self.server.getRoom(int(xmldict["id"]))

            if room is not None:
                self.room = room
                self.room.addUser(self)

        if request == "EXIT":
            if self.room is not None:
                self.room.removeUser(self)
                if self.player is not None:
                    self.room.exitGame(self.player)

                self.room = None
                self.player = None

                self.server.gotoLobby(self)

        if request == "CHAT":
            if self.room is None:
                return
            if xmldict["comment"] == "go":
                self.room.startGame()
            if xmldict["comment"] == "die":
                self.player.hp = 0
            if xmldict["comment"] == "sdie":
                builder = XMLBuilder("DIE")
                builder.player.name(self.name)
                self.sendXml(builder)
            if xmldict["comment"].startswith("fnd"):
                self.room.forceNextDeal = int(xmldict["comment"].split(" ")[1])
                
            self.room.sendChat(self.name, xmldict["comment"])

        if request == "ENTER_GAME":
            if self.room is None:
                return
            self.player = self.room.enterGame(self, xmldict["team"])

        if request == "EXIT_GAME":
            if self.room is None:
                return
            self.room.exitGame(self.player)
            self.player = None

        if request == "READY":
            if self.room is None:
                return
            self.player.ready = "isReady" in xmldict
            self.room.playerReady(self.player.name)

        if request == "BUY":
            if self.room is None:
                return
            response = "doBuy" in xmldict
            self.room.turn.playerBuyResponse(self.player, response)

        if request == "COMMAND":
            if self.room is None:
                return
            
            piece = xmldict["piece"] if "piece" in xmldict else []
            target = xmldict["@target"] if "@target" in xmldict else None

            if type(piece) is not list:
                piece = [piece]

            endInning = False

            piece = map(lambda x: self.server.itemManager.getItem(int(x.values()[0])), piece)
            if target is not None:
                endInning = self.room.turn.attackerCommand(self.player, piece, self.room.getPlayer(target))
            else:
                endInning = self.room.turn.defenderCommand(self.player, piece)

            while endInning:
                endInning = self.room.endInning()

            #self.transport.write("""<?xml version="1.0" encoding="UTF-8" standalone="no"?><COMMAND><piece><item>88</item></piece><commander><name>Igoor</name></commander><target><name>Odin</name></target></COMMAND>""" + chr(0))
            #self.transport.write("""<?xml version="1.0" encoding="UTF-8" standalone="no"?><COMMAND/><?xml version="1.0" encoding="UTF-8" standalone="no"?><COMMAND><piece><item>200</item></piece><isMiss/><commander><name>Igoor</name></commander><target><name>Robin Hood</name></target></COMMAND><?xml version="1.0" encoding="UTF-8" standalone="no"?><COMMAND><piece><item>200</item></piece><isMiss/><commander><name>Igoor</name></commander><target><name>Santa Claus</name></target></COMMAND><?xml version="1.0" encoding="UTF-8" standalone="no"?><DEAL><item>22</item></DEAL><?xml version="1.0" encoding="UTF-8" standalone="no"?><END_INNING/><?xml version="1.0" encoding="UTF-8" standalone="no"?><RESET_ATTACK_ORDER/><?xml version="1.0" encoding="UTF-8" standalone="no"?><START_INNING><attacker><name>Igoor</name></attacker></START_INNING>""".replace("<?xml", "\0<?xml") + chr(0))
