from twisted.web.server import Site
from twisted.web.resource import Resource
from twisted.internet import reactor, endpoints
from twisted.web.static import File

class CORSFile(File):
    def render_GET(self, request):
        request.setHeader(b"Access-Control-Allow-Origin", b"*")
        request.setHeader(b"Access-Control-Allow-Methods", b"GET, POST, OPTIONS")
        request.setHeader(b"Access-Control-Allow-Headers", b"Content-Type")
        return File.render_GET(self, request)

    def render_OPTIONS(self, request):
        request.setHeader(b"Access-Control-Allow-Origin", b"*")
        request.setHeader(b"Access-Control-Allow-Methods", b"GET, POST, OPTIONS")
        request.setHeader(b"Access-Control-Allow-Headers", b"Content-Type")
        request.setResponseCode(200)
        return b""

root = Resource()
root.putChild(b"game", CORSFile("./www.godfield.net/game"))
root.putChild(b"scripts", CORSFile("./www.godfield.net/scripts"))
root.putChild(b"stylesheets", CORSFile("./www.godfield.net/stylesheets"))
root.putChild(b"en.html", CORSFile("./www.godfield.net/en.html"))
root.putChild(b"favicon.ico", CORSFile("./www.godfield.net/favicon.ico"))
root.putChild(b"index.html", CORSFile("./www.godfield.net/index.html"))
root.putChild(b"crossdomain.xml", CORSFile("./static.godfield.net/crossdomain.xml"))
root.putChild(b"images", CORSFile("./static.godfield.net/images"))
root.putChild(b"sounds", CORSFile("./static.godfield.net/sounds"))

factory = Site(root)
endpoint = endpoints.TCP4ServerEndpoint(reactor, 80)
endpoint.listen(factory)
print("Server listening for new connections")
reactor.run()