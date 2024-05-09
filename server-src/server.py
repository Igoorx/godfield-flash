# type: ignore[reportGeneralTypeIssues]
from __future__ import annotations
from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from modules.session import Session
from modules.user import User, WebSocketUser
from modules.room import Room
from modules.item import ItemManager
from helpers.xmlbuilder import XMLBuilder

import argparse
from twisted.internet import reactor, protocol
from autobahn.twisted import websocket

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

    def getServerType(self, host) -> str:
        if self.mode != "ANY":
            return self.mode
        for type, port in self.typesPorts.items():
            if port == host.port:
                return type
        
    def getUser(self, name: str) -> Optional[Session]:
        for user in self.users:
            if user is not None and user.userName == name:
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
            bUser.name(user.userName)
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
        builder.user.name(user.userName)
        self.lobbyBroadXml(builder)

    def removeUser(self, user: Session):
        self.users.remove(user)

        builder = XMLBuilder("REMOVE_USER")
        builder.user.name(user.userName)
        self.lobbyBroadXml(builder)

    def createRoom(self, name: str, password: str = "", serverMode: str = "") -> Room:
        if serverMode == "":
            serverMode = self.mode
        assert self.mode == "ANY" or serverMode == self.mode

        room = Room(self, serverMode, name, password)

        self.lastRoomId += 1
        self.rooms[self.lastRoomId] = room
        room.id = self.lastRoomId

        return room
    
class WebSocketServer(websocket.WebSocketServerFactory, Server):
    protocol = WebSocketUser

    def __init__(self, mode: str, language: str, serverNumber: int):
        websocket.WebSocketServerFactory.__init__(self)
        Server.__init__(self, mode, language, serverNumber)

def main():
    parser = argparse.ArgumentParser(description="GodField Server")
    parser.add_argument('--mode', type=str, default="ANY", help='Server mode (default: ANY)')
    parser.add_argument('--language', type=str, default="EN", help='Server language (default: EN)')
    parser.add_argument('--number', type=int, default=1, help='Server number (default: 1)')
    parser.add_argument('--ws', action='store_true', help='Enable WebSocket mode (default: False)')

    args = parser.parse_args()

    if args.ws:
        factory = WebSocketServer(args.mode, args.language, args.number)
    else:
        factory = Server(args.mode, args.language, args.number)

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
