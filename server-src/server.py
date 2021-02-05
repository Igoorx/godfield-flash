from twisted.internet import reactor, protocol

from modules.game.user import User
from modules.game.bot import Bot
from modules.game.room import Room
from modules.itemManager import ItemManager
from helpers.xmlbuilder import XMLBuilder


class Server(protocol.ServerFactory):
    protocol = User

    def __init__(self, mode):
        self.mode = mode
        self.users = list()
        self.rooms = dict()
        self.lastRoomId = 0

        self.itemManager = ItemManager("ItemData.CSV")

    def getUser(self, name):
        for user in self.users:
            if user.name == name:
                return user
        return None

    def getRoom(self, id):
        if id not in self.rooms:
            return None
        return self.rooms[id]

    def lobbyBroadXml(self, xml):
        for user in self.users:
            if user.state == "LOBBY":
                user.sendXml(xml)

    def buildLobbyXml(self):
        builder = XMLBuilder("ENTER")
        builder.lobby  # <lobby />

        for user_ in self.users:
            bUser = builder.user
            bUser.name(user_.name)
            if user_.room is not None:
                bUser.roomID(str(user_.room.id))
        
        for room in self.rooms.values():
            bRoom = builder.room
            bRoom.name(room.name)
            if room.password != str():
                bRoom.hasPassword  # <hasPassword />
            bRoom.id(str(room.id))
            bRoom.language(room.language)
            bRoom.playersLimit(str(room.playersLimit))
            bRoom.time(str(room.time))
            if room.playing:
                bRoom.isPlaying  # <isPlaying />
            for player in room.players:
                bPlayer = bRoom.player
                bPlayer.name(player.name)
                bPlayer.team(player.team)
                if player.dead and room.playing:
                    bPlayer.isDead  # <isDead />

        return builder

    def addUser(self, user):
        self.users.append(user)

        builder = XMLBuilder("ADD_USER")
        builder.user.name(user.name)
        self.lobbyBroadXml(builder)

    def removeUser(self, user):
        self.users.remove(user)

        builder = XMLBuilder("REMOVE_USER")
        builder.user.name(user.name)
        self.lobbyBroadXml(builder)

    def createRoom(self, name):
        room = Room(self, name)

        #for i in range(4):
        #    b = Bot(''.join(__import__("random").choice(__import__("string").ascii_uppercase + __import__("string").digits) for _ in range(12)), "SINGLE")
        #    b.server = self
        #    room.players.append(b)
        #    b.room = room
        #    b.ready = True

        self.lastRoomId += 1
        self.rooms[self.lastRoomId] = room
        room.id = self.lastRoomId

        return room


def main():
    serverMode = argv[1] if len(argv) > 1 else "FREEFIGHT"

    if serverMode not in ["TRAINING", "FREEFIGHT", "PRIVATEFREEFIGHT"]:
        print "WARNING: Invalid server mode \""+serverMode+"\""
        serverMode = "FREEFIGHT"

    factory = Server(serverMode)
    reactor.listenTCP(58251, factory)
    reactor.listenTCP(58151, factory) #EN_FREEFIGHT
    reactor.listenTCP(58101, factory)
    reactor.listenTCP(58001, factory) #TRAINING
    reactor.listenTCP(853, factory)

    print "Server listening in port 58151"
    reactor.run()

# this only runs if the module was *not* imported
if __name__ == '__main__':
    from sys import argv
    main()
