from twisted.internet import reactor, protocol

from helpers.xmltodict import parse as xmltodict
from helpers.xmlbuilder import XMLBuilder

from modules.game.session import Session


class User(protocol.Protocol):
    def __init__(self):
        self.recvd = str()

        self.server = None
        self.session = None

    def connectionMade(self):
        self.server = self.factory

    def connectionLost(self, reason):
        if self.session is not None:
            self.session.onDisconnect()
    
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
        if self.session is not None:
            print "SEND ("+self.session.name+"):", repr(str(xml))
        self.transport.write(str(xml) + chr(0))

    def parseXml(self, xml):
        xmldict = xmltodict(xml)
        request = xmldict.keys()[0]
        xmldict = xmldict.values()[0] if xmldict.values()[0] != None else dict()

        #print repr(xml)
        #print "RECV ("+self.session.name+"):", request, xmldict

        #<player><name>Igoor</name><team>SINGLE</team><isReady/><power key="HP">90</power><power key="MP">90</power><power key="YEN">90</power></player><player><name>Sinbad</name><team>SINGLE</team><isReady/><power key="HP">40</power><power key="MP">10</power><power key="YEN">20</power></player><player><name>Santa Claus</name><team>SINGLE</team><isReady/><power key="HP">40</power><power key="MP">10</power><power key="YEN">20</power></player><player><name>Odin</name><team>SINGLE</team><isReady/><power key="HP">40</power><power key="MP">10</power><power key="YEN">20</power></player></players><privatePlayer/></game></room></ENTER>""" + chr(0))

        if request == "ERROR":
            print repr(xml)
            print request, xmldict

        elif request == "LOGIN":
            name = xmldict["name"]

            if self.server.getUser(name):
                self.transport.loseConnection()
                return

            self.session = Session(self, xmldict)
            self.session.onLogin()

        else:
            if self.session is None:
                self.transport.loseConnection()
                return
            
            self.session.onRequest(request, xmldict)