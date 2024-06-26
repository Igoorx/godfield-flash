# type: ignore[reportGeneralTypeIssues]
from __future__ import annotations
from typing import TYPE_CHECKING, Any, Optional
if TYPE_CHECKING:
    from server import Server
from helpers.xmltodict import parse as xmltodict
from modules.session import Session

from twisted.internet import protocol
from autobahn.twisted import websocket

__all__ = ("User", "WebSocketUser")


class User(protocol.Protocol):
    server: Server
    recvd: str
    ipAddress: str
    session: Optional[Session]

    __slots__ = tuple(__annotations__)

    def __init__(self):
        self.recvd = str()
        self.session = None

    def connectionMade(self):
        self.server = self.factory
        self.ipAddress = self.transport.getPeer().host

    def connectionLost(self, reason):
        if self.session is not None:
            self.session.onDisconnect()
    
    def dataReceived(self, data):
        data = data.decode()

        if data == "<policy-file-request/>\0":
            self.sendPayload(b"<cross-domain-policy><allow-access-from domain=\"*\" to-ports=\"*\" /></cross-domain-policy>\0")
            self.transport.loseConnection()
            return

        self.recvd += data

        if not data.endswith("\0"):
            return

        xmls = self.recvd.split("\0")
        for xml in xmls:
            if len(xml) == 0:
                break
            xml = xml.replace("\n", " ")
            self.parseXml(xml)

        self.recvd = str()

    def sendPayload(self, payload):
        self.transport.write(payload)

    def sendXml(self, xml):
        if self.session is not None:
            print(f"SEND ({self.session.userName}): {repr(str(xml))}")
        self.sendPayload((str(xml) + chr(0)).encode())

    def parseXml(self, xml: str):
        xmldict: Any = xmltodict(xml)
        request = list(xmldict.keys())[0]
        xmldict = list(xmldict.values())[0] if list(xmldict.values())[0] != None else dict()

        #print repr(xml)
        print(f"RECV \"{request}\" from {self.session.userName if self.session else '?'}: {xmldict}")

        if request == "ERROR":
            print(repr(xml))
            print(request, xmldict)

        elif request == "LOGIN":
            if self.session is not None:
                self.transport.loseConnection()
                return

            name = xmldict["name"]

            if self.server.getUser(name):
                self.transport.loseConnection()
                return

            serverMode = self.server.getServerType(self.transport.getHost())

            self.session = Session(self, xmldict)
            self.session.onLogin(serverMode)

        else:
            if self.session is None:
                self.transport.loseConnection()
                return
            
            self.session.onRequest(request, xmldict)

class WebSocketUser(websocket.WebSocketServerProtocol, User):
    def __init__(self):
        websocket.WebSocketServerProtocol.__init__(self)
        User.__init__(self)

    def onOpen(self):
        User.connectionMade(self)

    def onClose(self, wasClean, code, reason):
        User.connectionLost(self, reason)

    def onMessage(self, payload, isBinary):
        assert isBinary, "Binary message expected."
        User.dataReceived(self, payload)

    def sendPayload(self, payload):
        if self.state != websocket.protocol.WebSocketProtocol.STATE_OPEN:
            return
        self.sendMessage(payload, True)