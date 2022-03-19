from twisted.web.server import Site
from twisted.web.resource import Resource
from twisted.internet import reactor, endpoints
from twisted.web.static import File

root = Resource()
root.putChild(b"game", File("./www.godfield.net/game"))
root.putChild(b"scripts", File("./www.godfield.net/scripts"))
root.putChild(b"stylesheets", File("./www.godfield.net/stylesheets"))
root.putChild(b"en.html", File("./www.godfield.net/en.html"))
root.putChild(b"favicon.ico", File("./www.godfield.net/favicon.ico"))
root.putChild(b"index.html", File("./www.godfield.net/index.html"))
root.putChild(b"crossdomain.xml", File("./static.godfield.net/crossdomain.xml"))
root.putChild(b"images", File("./static.godfield.net/images"))
root.putChild(b"sounds", File("./static.godfield.net/sounds"))

factory = Site(root)
endpoint = endpoints.TCP4ServerEndpoint(reactor, 80)
endpoint.listen(factory)
print("Server listening for new connections")
reactor.run()