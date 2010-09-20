# neubot/rendezvous.py
# Copyright (c) 2010 NEXA Center for Internet & Society

# This file is part of Neubot.
#
# Neubot is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Neubot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Neubot.  If not, see <http://www.gnu.org/licenses/>.

#
# Rendez-vous with master node to discover other peers and to
# get information on available software updates.
# This is the command that is executed by default if you don't
# pass a command to neubot(1).
#

if __name__ == "__main__":
    from sys import path
    path.insert(0, ".")

from neubot.http.servers import Server
from neubot.http.messages import Message
from neubot.http.clients import Client
from neubot.http.clients import ClientController
from neubot.speedtest import SpeedtestController
from neubot.speedtest import SpeedtestClient
from xml.etree.ElementTree import ElementTree
from xml.etree.ElementTree import TreeBuilder
from neubot.http.messages import compose
from ConfigParser import SafeConfigParser
from neubot.net.pollers import sched
from neubot.database import database
from neubot.speedtest import speedtest
from neubot.utils import versioncmp
from neubot.net.pollers import loop
from xml.dom import minidom
from StringIO import StringIO
from neubot import version
from neubot.ui import ui
from neubot import log
from getopt import GetoptError
from getopt import getopt
from neubot.state import state
from os import environ
from sys import argv
from sys import stdout
from sys import stderr

# unclean
from neubot.speedtest import XML_get_scalar
from neubot.speedtest import XML_get_vector

#
# <rendezvous>
#  <accept>speedtest</accept>
#  <accept>bittorrent</accept>
#  <version>0.2.3</version>
# </rendezvous>
#

class XMLRendezvous:
    def __init__(self):
        self.accept = []
        self.version = ""

    def parse(self, stringio):
        tree = ElementTree()
        try:
            tree.parse(stringio)
        except:
            raise ValueError("Can't parse XML body")
        else:
            self.accept = XML_get_vector(tree, "accept")
            self.version = XML_get_scalar(tree, "version")

class RendezvousServer(Server):
    def __init__(self, config):
        self.config = config
        Server.__init__(self, config.address, port=config.port)

    def bind_failed(self):
        log.error("Is another neubot(1) running?")
        exit(1)

    def got_request(self, connection, request):
        try:
            self.process_request(connection, request)
        except KeyboardInterrupt:
            raise
        except:
            log.exception()
            response = Message()
            compose(response, code="500", reason="Internal Server Error")
            connection.reply(request, response)

    def process_request(self, connection, request):
        if request.uri == "/rendezvous":
            self._do_rendezvous(connection, request)
            return
        response = Message()
        compose(response, code="403", reason="Forbidden")
        connection.reply(request, response)

    def _do_rendezvous(self, connection, request):
        builder = TreeBuilder()
        m = XMLRendezvous()
        m.parse(request.body)
        builder.start("rendezvous_response", {})
        if m.version:
            if versioncmp(version, m.version) > 0:
                builder.start("update", {"uri": self.config.update_uri})
                builder.data(version)
                builder.end("update")
        if "speedtest" in m.accept:
            builder.start("available", {"name": "speedtest"})
            builder.start("uri", {})
#           builder.data("http://speedtest1.neubot.org/speedtest")
#           builder.data("http://speedtest2.neubot.org/speedtest")
            builder.data(self.config.test_uri)
            builder.end("uri")
            builder.end("available")
        builder.end("rendezvous_response")
        root = builder.close()
        tree = ElementTree(root)
        stringio = StringIO()
        tree.write(stringio, encoding="utf-8")
        stringio.seek(0)
        # HTTP
        response = Message()
        compose(response, code="200", reason="Ok",
                mimetype="text/xml", body=stringio)
        connection.reply(request, response)

#
# [rendezvous]
# address: 0.0.0.0
# update_uri: http://releases.neubot.org/latest
# test_uri: http://speedtest1.neubot.org/speedtest
# port: 9773
#

#
# TODO Still unsure about the URI that should be used
# here by default.
#

class RendezvousConfig(SafeConfigParser):
    def __init__(self):
        SafeConfigParser.__init__(self)
        self.address = "0.0.0.0"
        self.update_uri = "http://releases.neubot.org/latest"
        self.test_uri = "http://speedtest1.neubot.org/speedtest"
        self.port = "9773"

#   def check(self):
#       pass

    def readfp(self, fp, filename=None):
        SafeConfigParser.readfp(self, fp, filename)
        self._do_parse()

    def _do_parse(self):
        if self.has_option("rendezvous", "address"):
            self.address = self.get("rendezvous", "address")
        if self.has_option("rendezvous", "update_uri"):
            self.update_uri = self.get("rendezvous", "update_uri")
        if self.has_option("rendezvous", "test_uri"):
            self.test_uri = self.get("rendezvous", "test_uri")
        if self.has_option("rendezvous", "port"):
            self.port = self.get("rendezvous", "port")

    def read(self, filenames):
        SafeConfigParser.read(self, filenames)
        self._do_parse()

class RendezvousModule:
    def __init__(self):
        self.config = RendezvousConfig()
        self.server = None

    def configure(self, filenames, fakerc):
        self.config.read(filenames)
        self.config.readfp(fakerc)
        # XXX other modules need to read() it too
        fakerc.seek(0)

    def start(self):
        self.server = RendezvousServer(self.config)
        self.server.listen()

rendezvous = RendezvousModule()

#
# <rendezvous_response>
#  <available name="speedtest">
#   <uri>http://speedtest1.neubot.org/speedtest</uri>
#   <uri>http://speedtest2.neubot.org/speedtest</uri>
#  </available>
#  <update uri="http://releases.neubot.org/neubot-0.2.4.exe">0.2.4</update>
# </rendezvous_response>
#

def _XML_parse_available(tree):
    available = {}
    elements = tree.findall("available")
    for element in elements:
        name = element.get("name")
        if not name:
            continue
        vector = []
        uris = element.findall("uri")
        for uri in uris:
            vector.append(uri.text)
        if not uris:
            continue
        available[name] = vector
    return available

# sloppy
def _XML_parse_update(tree):
    update = {}
    elements = tree.findall("update")
    for element in elements:
        uri = element.get("uri")
        if not uri:
            continue
        ver = element.text
        update[ver] = uri
    return update

class XMLRendezvous_Response:
    def __init__(self):
        self.available = {}
        self.update = {}

    def __del__(self):
        pass

    def parse(self, stringio):
        tree = ElementTree()
        try:
            tree.parse(stringio)
        except:
            log.exception()
            raise ValueError("Can't parse XML body")
        else:
            self.available = _XML_parse_available(tree)
            self.update = _XML_parse_update(tree)

#
# Not the best prettyprint in the world because it would
# be way more nice to have the tags of text-only elements
# on the same line of the text itself, e.g.:
#  <tag>texttexttext</tag>
# But better than spitting out a linearized XML.
#

def _XML_prettyprint(stringio):
    stringio.seek(0)
    document = minidom.parse(stringio)
    stringio.seek(0)
    return document.toprettyxml(indent=" ",
     newl="\r\n", encoding="utf-8")

FLAG_TESTING = 1<<0

class RendezvousClient(ClientController, SpeedtestController):
    def __init__(self, server_uri, interval, dontloop, xdebug):
        self.server_uri = server_uri
        self.interval = interval
        self.dontloop = dontloop
        self.xdebug = xdebug
        self.flags = 0

    def __del__(self):
        pass

    def _reschedule(self):
        state.set_inactive()
        if self.flags & FLAG_TESTING:
            return
        if self.dontloop:
            return
        log.info("* Next rendezvous in %d seconds" % self.interval)
        sched(self.interval, self.rendezvous)

    def connection_failed(self, client):
        self._reschedule()

    def connection_lost(self, client):
        self._reschedule()

    def rendezvous(self):
        state.set_activity("rendezvous")
        self._prepare_tree()

    def _prepare_tree(self):
        builder = TreeBuilder()
        builder.start("rendezvous", {})
        builder.start("accept", {})
        builder.data("speedtest")
        builder.end("accept")
        builder.end("rendezvous")
        root = builder.close()
        self._serialize_tree(root)

    def _serialize_tree(self, root):
        tree = ElementTree(root)
        stringio = StringIO()
        tree.write(stringio, encoding="utf-8")
        stringio.seek(0)
        if self.xdebug:
            stdout.write(_XML_prettyprint(stringio))
        self._send_http_request(stringio)

    def _send_http_request(self, stringio):
        request = Message()
        compose(request, method="GET", uri=self.server_uri,
         mimetype="text/xml", body=stringio, keepalive=False)
        client = Client(self)
        client.sendrecv(request)

    def got_response(self, client, request, response):
        if response.code != "200":
            log.error("Error: %s %s" % (response.code, response.reason))
            self._reschedule()
            return
        self._parse_response(response)

    def _parse_response(self, response):
        if self.xdebug:
            stdout.write(_XML_prettyprint(response.body))
        m = XMLRendezvous_Response()
        try:
            m.parse(response.body)
        except ValueError:
            log.exception()
            self._reschedule()
        else:
            self._do_followup(m)

    def _do_followup(self, m):
        if m.update:
            for ver, uri in m.update.items():
                log.warning("Version %s available at %s" % (ver, uri))
        if self.xdebug:
            self._reschedule()
            return
        if m.available.has_key("speedtest"):
            uri = m.available["speedtest"][0]
            self.flags |= FLAG_TESTING
            self.start_speedtest_simple(uri)

    def speedtest_complete(self):
        self.flags &= ~FLAG_TESTING
        self._reschedule()

USAGE = 								\
"Usage: @PROGNAME@ -V\n"						\
"       @PROGNAME@ --help\n"						\
"       @PROGNAME@ [-nvx] [-T interval] [master-URI]\n"			\
"       @PROGNAME@ -S [-v] [-D name=value]\n"

HELP = USAGE +								\
"Options:\n"								\
"  -D name=value : Set configuration file property.\n"			\
"  --help        : Print this help screen and exit.\n"			\
"  -n            : Don't loop, just rendez-vous once.\n"		\
"  -S            : Run the program in server mode.\n"			\
"  -T interval   : Interval between each rendez-vous.\n"		\
"  -V            : Print version number and exit.\n"			\
"  -v            : Run the program in verbose mode.\n"			\
"  -x            : Debug mode, don't run any test.\n"

def main(args):
    fakerc = StringIO()
    fakerc.write("[rendezvous]\n")
    dontloop = False
    servermode = False
    interval = 300
    xdebug = False
    # parse
    try:
        options, arguments = getopt(args[1:], "D:nST:Vvx", ["help"])
    except GetoptError:
        stderr.write(USAGE.replace("@PROGNAME@", args[0]))
        exit(1)
    # options
    for name, value in options:
        if name == "-D":
            fakerc.write(value + "\n")
        elif name == "--help":
            stdout.write(HELP.replace("@PROGNAME@", args[0]))
            exit(1)
        elif name == "-n":
            dontloop = True
        elif name == "-S":
            servermode = True
        elif name == "-T":
            try:
                interval = int(value)
            except ValueError:
                interval = -1
            if interval <= 0:
                log.error("Invalid argument to -T: %s" % value)
                exit(1)
        elif name == "-V":
            stdout.write(version + "\n")
            exit(0)
        elif name == "-v":
            log.verbose()
        elif name == "-x":
            xdebug = True
    # options
    fakerc.seek(0)
    filenames = ["/etc/neubot/config"]
    if environ.has_key("HOME"):
        filenames.append(environ["HOME"] + "/.neubot/config")
    database.configure(filenames, fakerc)
    rendezvous.configure(filenames, fakerc)
    speedtest.configure(filenames, fakerc)
    ui.configure(filenames, fakerc)
    # server
    if servermode:
        if len(arguments) > 0:
            stderr.write(USAGE.replace("@PROGNAME@", args[0]))
            exit(1)
        database.start()
        rendezvous.start()
        speedtest.start()
        loop()
        exit(0)
    # client
    if len(arguments) != 1:
        stderr.write(USAGE.replace("@PROGNAME@", args[0]))
        exit(1)
    uri = arguments[0]
    database.start()
    if not dontloop and not xdebug:
        ui.start()
    client = RendezvousClient(uri, interval, dontloop, xdebug)
    client.rendezvous()
    loop()

if __name__ == "__main__":
    main(argv)
