# type: ignore[reportGeneralTypeIssues]
from __future__ import annotations
from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from modules.game.session import Session
from modules.game.user import User
from modules.game.room import Room
from modules.item import ItemManager
from helpers.xmlbuilder import XMLBuilder

from twisted.internet import reactor, protocol

__all__ = ("Server",)


class Server(protocol.ServerFactory):
    mode: str
    language: str
    serverNumber: int
    users: list[Session]
    rooms: dict[int, Room]
    lastRoomId: int
    itemManager: ItemManager
    typesPorts: dict[str, int]

    __slots__ = tuple(__annotations__)

    protocol = User

    def __init__(self, mode: str, language: str, serverNumber: int):
        self.mode = mode
        self.language = language
        self.serverNumber = serverNumber
        self.users = list()
        self.rooms = dict()
        self.lastRoomId = 0

        self.itemManager = ItemManager("ItemData.CSV", "AssistantItemData.CSV")

        self.typesPorts = dict()

        def setServerType(type: str, port: int):
            self.typesPorts[type] = port + self.serverNumber
        setServerType("TRAINING", 58000)
        setServerType("FREE_FIGHT_PRIVATE", 58200 if self.language == "JP" else 58250)
        setServerType("FREE_FIGHT", 58100 if self.language == "JP" else 58150)
        setServerType("DUEL", 58300)
        setServerType("SPIRIT", 58400)
        
        if self.mode != "ANY" and self.mode not in self.typesPorts:
            print(f"WARNING: Invalid server mode \"{self.mode}\", using default server mode (ANY).")
            self.mode = "ANY"
        
    def getUser(self, name: str) -> Optional[Session]:
        for user in self.users:
            if user is not None and user.name == name:
                return user
        return None

    def getRoom(self, id: int) -> Optional[Room]:
        if id in self.rooms:
            return self.rooms[id]
        return None

    def lobbyBroadXml(self, xml):
        for user in self.users:
            if user is not None and user.state == "LOBBY":
                user.sendXml(xml)

    def buildLobbyXml(self) -> XMLBuilder:
        builder = XMLBuilder("ENTER")
        builder.lobby  # <lobby />

        for user in self.users:
            bUser = builder.user
            bUser.name(user.name)
            if user.room is not None:
                bUser.roomID(str(user.room.id))
        
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

    def addUser(self, user: Session):
        self.users.append(user)

        builder = XMLBuilder("ADD_USER")
        builder.user.name(user.name)
        self.lobbyBroadXml(builder)

    def removeUser(self, user: Session):
        self.users.remove(user)

        builder = XMLBuilder("REMOVE_USER")
        builder.user.name(user.name)
        self.lobbyBroadXml(builder)

    def createRoom(self, name: str, password: str = "") -> Room:
        room = Room(self, name, password)

        self.lastRoomId += 1
        self.rooms[self.lastRoomId] = room
        room.id = self.lastRoomId

        return room


def main():
    serverMode = argv[1] if len(argv) > 1 else "ANY"
    serverLanguage = argv[2] if len(argv) > 2 else "EN"
    serverNumber = int(argv[3]) if len(argv) > 3 else 1
        
    factory = Server(serverMode, serverLanguage, serverNumber)

    if factory.mode == "ANY":
        for port in factory.typesPorts.values():
            reactor.listenTCP(port, factory)
    else:
        reactor.listenTCP(factory.typesPorts[factory.mode], factory)

    print("Server listening for new connections")
    reactor.run()

# this only runs if the module was *not* imported
if __name__ == '__main__':
    from sys import argv
    main()
