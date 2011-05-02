# neubot/net/stream.py

#
# Copyright (c) 2010-2011 Simone Basso <bassosimone@gmail.com>,
#  NEXA Center for Internet & Society at Politecnico di Torino
#
# This file is part of Neubot <http://www.neubot.org/>.
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

import collections
import errno
import os
import socket
import sys
import types

try:
    import ssl
except ImportError:
    ssl = None

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.config import CONFIG
from neubot.net.poller import Pollable
from neubot.net.measurer import MEASURER
from neubot.net.poller import POLLER
from neubot.arcfour import arcfour_new
from neubot.log import LOG
from neubot import system
from neubot import utils
from neubot import boot

SUCCESS = 0
ERROR = 1
WANT_READ = 2
WANT_WRITE = 3

TIMEOUT = 300

MAXBUF = 1<<18

SOFT_ERRORS = [ errno.EAGAIN, errno.EWOULDBLOCK, errno.EINTR ]

# Winsock returns EWOULDBLOCK
INPROGRESS = [ 0, errno.EINPROGRESS, errno.EWOULDBLOCK, errno.EAGAIN ]

if ssl:


    class SSLWrapper(object):
        def __init__(self, sock):
            self.sock = sock

        def soclose(self):
            try:
                self.sock.close()
            except ssl.SSLError:
                LOG.exception()

        def sorecv(self, maxlen):
            try:
                octets = self.sock.read(maxlen)
                return SUCCESS, octets
            except ssl.SSLError, exception:
                if exception[0] == ssl.SSL_ERROR_WANT_READ:
                    return WANT_READ, ""
                elif exception[0] == ssl.SSL_ERROR_WANT_WRITE:
                    return WANT_WRITE, ""
                else:
                    return ERROR, exception

        def sosend(self, octets):
            try:
                count = self.sock.write(octets)
                return SUCCESS, count
            except ssl.SSLError, exception:
                if exception[0] == ssl.SSL_ERROR_WANT_READ:
                    return WANT_READ, 0
                elif exception[0] == ssl.SSL_ERROR_WANT_WRITE:
                    return WANT_WRITE, 0
                else:
                    return ERROR, exception


class SocketWrapper(object):
    def __init__(self, sock):
        self.sock = sock

    def soclose(self):
        try:
            self.sock.close()
        except socket.error:
            LOG.exception()

    def sorecv(self, maxlen):
        try:
            octets = self.sock.recv(maxlen)
            return SUCCESS, octets
        except socket.error, exception:
            if exception[0] in SOFT_ERRORS:
                return WANT_READ, ""
            else:
                return ERROR, exception

    def sosend(self, octets):
        try:
            count = self.sock.send(octets)
            return SUCCESS, count
        except socket.error, exception:
            if exception[0] in SOFT_ERRORS:
                return WANT_WRITE, 0
            else:
                return ERROR, exception


class Stream(Pollable):

    """To implement the protocol syntax, subclass this class and
       implement the finite state machine described in the file
       `doc/protocol.png`.  The low level finite state machines for
       the send and recv path are documented, respectively, in
       `doc/sendpath.png` and `doc/recvpath.png`."""

    def __init__(self, poller):
        self.poller = poller
        self.parent = None

        self.sock = None
        self.filenum = -1
        self.myname = None
        self.peername = None
        self.logname = None

        self.timeout = TIMEOUT
        self.encrypt = None
        self.decrypt = None

        self.send_octets = None
        self.send_queue = collections.deque()
        self.send_ticks = 0
        self.recv_maxlen = 0
        self.recv_ticks = 0

        self.eof = False
        self.isclosed = 0
        self.send_pending = 0
        self.sendblocked = 0
        self.recv_pending = 0
        self.recvblocked = 0
        self.kickoffssl = 0

        self.measurer = None
        self.bytes_recv_tot = 0
        self.bytes_sent_tot = 0
        self.bytes_recv = 0
        self.bytes_sent = 0

        self.conf = None

    def fileno(self):
        return self.filenum

    def attach(self, parent, sock, conf, measurer=None):

        self.parent = parent
        self.conf = conf

        self.filenum = sock.fileno()
        self.myname = sock.getsockname()
        self.peername = sock.getpeername()
        self.logname = str((self.myname, self.peername))

        self.measurer = measurer
        if self.measurer:
            self.measurer.register_stream(self)

        LOG.debug("* Connection made %s" % str(self.logname))

        if conf.get("net.stream.secure", False):
            if not ssl:
                raise RuntimeError("SSL support not available")

            server_side = conf.get("net.stream.server_side", False)
            certfile = conf.get("net.stream.certfile", None)

            so = ssl.wrap_socket(sock, do_handshake_on_connect=False,
              certfile=certfile, server_side=server_side)
            self.sock = SSLWrapper(so)

            if not server_side:
                self.kickoffssl = 1

        else:
            self.sock = SocketWrapper(sock)

        if conf.get("net.stream.obfuscate", False):
            key = conf.get("net.stream.key", None)
            self.encrypt = arcfour_new(key).encrypt
            self.decrypt = arcfour_new(key).decrypt

        self.connection_made()

    def connection_made(self):
        pass

    # Close path

    def connection_lost(self, exception):
        pass

    def closed(self, exception=None):
        self._do_close(exception)

    def shutdown(self):
        self._do_close()

    def _do_close(self, exception=None):
        if self.isclosed:
            return

        self.isclosed = 1

        if exception:
            LOG.error("* Connection %s: %s" % (self.logname, exception))
        elif self.eof:
            LOG.debug("* Connection %s: EOF" % (self.logname))
        else:
            LOG.debug("* Closed connection %s" % (self.logname))

        self.connection_lost(exception)
        if self.parent:
            self.parent.connection_lost(self)

        if self.measurer:
            self.measurer.unregister_stream(self)

        self.send_octets = None
        self.send_ticks = 0
        self.recv_maxlen = 0
        self.recv_ticks = 0
        self.sock.soclose()

        self.poller.close(self)

    # Timeouts

    def readtimeout(self, now):
        return (self.recv_pending and (now - self.recv_ticks) > self.timeout)

    def writetimeout(self, now):
        return (self.send_pending and (now - self.send_ticks) > self.timeout)

    # Recv path

    def start_recv(self, maxlen=MAXBUF):
        if self.isclosed:
            return
        if self.recv_pending:
            return

        self.recv_maxlen = maxlen
        self.recv_ticks = utils.ticks()
        self.recv_pending = 1

        if self.recvblocked:
            return

        self.poller.set_readable(self)

        #
        # The client-side of an SSL connection must send the HELLO
        # message to start the negotiation.  This is done automagically
        # by SSL_read and SSL_write.  When the client first operation
        # is a send(), no problem: the socket is always writable at
        # the beginning and writable() invokes sosend() that invokes
        # SSL_write() that negotiates.  The problem is when the client
        # first operation is recv(): in this case the socket would never
        # become readable because the server side is waiting for an HELLO.
        # The following piece of code makes sure that the first recv()
        # of the client invokes readable() that invokes sorecv() that
        # invokes SSL_read() that starts the negotiation.
        #

        if self.kickoffssl:
            self.kickoffssl = 0
            self.readable()

    def readable(self):
        if self.recvblocked:
            self.poller.set_writable(self)
            if not self.recv_pending:
                self.poller.unset_readable(self)
            self.recvblocked = 0
            self.writable()
            return

        status, octets = self.sock.sorecv(self.recv_maxlen)

        if status == SUCCESS and octets:

            self.bytes_recv_tot += len(octets)
            self.bytes_recv += len(octets)

            self.recv_maxlen = 0
            self.recv_ticks = 0
            self.recv_pending = 0
            self.poller.unset_readable(self)

            if self.decrypt:
                octets = self.decrypt(octets)

            self.recv_complete(octets)
            return

        if status == WANT_READ:
            return

        if status == WANT_WRITE:
            self.poller.unset_readable(self)
            self.poller.set_writable(self)
            self.sendblocked = 1
            return

        if status == SUCCESS and not octets:
            self.eof = True
            self._do_close()
            return

        if status == ERROR:
            # Here octets is the exception that occurred
            self._do_close(octets)
            return

        raise RuntimeError("Unexpected status value")

    def recv_complete(self, octets):
        pass

    # Send path

    def start_send(self, octets):
        if self.isclosed:
            return

        if type(octets) == types.UnicodeType:
            LOG.oops("Received unicode input")
            octets = octets.encode("utf-8")
        if self.encrypt:
            octets = self.encrypt(octets)

        if self.send_pending:
            self.send_queue.append(octets)
            return

        self.send_octets = octets
        self.send_ticks = utils.ticks()
        self.send_pending = 1

        if self.sendblocked:
            return

        self.poller.set_writable(self)

    def writable(self):
        if self.sendblocked:
            self.poller.set_readable(self)
            if not self.send_pending:
                self.poller.unset_writable(self)
            self.sendblocked = 0
            self.readable()
            return

        status, count = self.sock.sosend(self.send_octets)

        if status == SUCCESS and count > 0:

            self.bytes_sent_tot += count
            self.bytes_sent += count

            if count == len(self.send_octets):

                if len(self.send_queue) > 0:
                    self.send_octets = self.send_queue.popleft()
                    self.send_ticks = utils.ticks()
                    return

                self.send_octets = None
                self.send_ticks = 0
                self.send_pending = 0
                self.poller.unset_writable(self)

                self.send_complete()
                return

            if count < len(self.send_octets):
                self.send_octets = buffer(self.send_octets, count)
                self.send_ticks = utils.ticks()
                self.poller.set_writable(self)
                return

            raise RuntimeError("Sent more than expected")

        if status == WANT_WRITE:
            return

        if status == WANT_READ:
            self.poller.unset_writable(self)
            self.poller.set_readable(self)
            self.recvblocked = 1
            return

        if status == ERROR:
            # Here count is the exception that occurred
            self._do_close(count)
            return

        if status == SUCCESS and count <= 0:
            raise RuntimeError("Unexpected count value")

        raise RuntimeError("Unexpected status value")

    def send_complete(self):
        pass


class Connector(Pollable):

    def __init__(self, poller, parent):
        self.poller = poller
        self.parent = parent
        self.sock = None
        self.timeout = 15
        self.timestamp = 0
        self.endpoint = None
        self.family = 0
        self.measurer = None

    def connect(self, endpoint, conf, measurer=None):
        self.endpoint = endpoint
        self.family = socket.AF_INET
        if conf.get("net.stream.ipv6", False):
            self.family = socket.AF_INET6
        self.measurer = measurer
        rcvbuf = conf.get("net.stream.rcvbuf", 262144)
        sndbuf = conf.get("net.stream.sndbuf", 0)

        try:
            addrinfo = socket.getaddrinfo(endpoint[0], endpoint[1],
                                          self.family, socket.SOCK_STREAM)
        except socket.error, exception:
            LOG.error("* Connection to %s failed: %s" % (endpoint, exception))
            self.parent._connection_failed(self, exception)
            return

        last_exception = None
        for family, socktype, protocol, cannonname, sockaddr in addrinfo:
            try:

                sock = socket.socket(family, socktype, protocol)
                if rcvbuf:
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, rcvbuf)
                if sndbuf:
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, sndbuf)
                sock.setblocking(False)
                result = sock.connect_ex(sockaddr)
                if result not in INPROGRESS:
                    raise socket.error(result, os.strerror(result))

                self.sock = sock
                self.timestamp = utils.ticks()
                self.poller.set_writable(self)
                if result != 0:
                    LOG.debug("* Connecting to %s ..." % str(endpoint))
                    self.parent.started_connecting(self)
                return

            except socket.error, exception:
                last_exception = exception

        LOG.error("* Connection to %s failed: %s" % (endpoint, last_exception))
        self.parent._connection_failed(self, last_exception)

    def fileno(self):
        return self.sock.fileno()

    def writable(self):
        self.poller.unset_writable(self)

        # See http://cr.yp.to/docs/connect.html
        try:
            self.sock.getpeername()
        except socket.error, exception:
            if exception[0] == errno.ENOTCONN:
                try:
                    self.sock.recv(MAXBUF)
                except socket.error, exception2:
                    exception = exception2
            self.parent._connection_failed(self, exception)
            return

        if self.measurer:
            rtt = utils.ticks() - self.timestamp
            self.measurer.rtts.append(rtt)

        self.parent._connection_made(self.sock)

    def writetimeout(self, now):
        return now - self.timestamp >= self.timeout

    def closing(self, exception=None):
        LOG.error("* Connection to %s failed: %s" % (self.endpoint, exception))
        self.parent._connection_failed(self, exception)


class Listener(Pollable):

    def __init__(self, poller, parent):
        self.poller = poller
        self.parent = parent
        self.lsock = None
        self.endpoint = None
        self.family = 0

    def listen(self, endpoint, conf):
        self.endpoint = endpoint
        self.family = socket.AF_INET
        if conf.get("net.stream.ipv6", False):
            self.family = socket.AF_INET6
        rcvbuf = conf.get("net.stream.rcvbuf", 262144)
        sndbuf = conf.get("net.stream.sndbuf", 0)

        try:
            addrinfo = socket.getaddrinfo(endpoint[0], endpoint[1],
              self.family, socket.SOCK_STREAM, 0, socket.AI_PASSIVE)
        except socket.error, exception:
            LOG.error("* Bind %s failed: %s" % (self.endpoint, exception))
            self.parent.bind_failed(self, exception)
            return

        last_exception = None
        for family, socktype, protocol, canonname, sockaddr in addrinfo:
            try:

                lsock = socket.socket(family, socktype, protocol)
                lsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                if rcvbuf:
                    lsock.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF,rcvbuf)
                if sndbuf:
                    lsock.setsockopt(socket.SOL_SOCKET,socket.SO_SNDBUF,sndbuf)
                lsock.setblocking(False)
                lsock.bind(sockaddr)
                # Probably the backlog here is too big
                lsock.listen(128)

                LOG.debug("* Listening at %s" % str(self.endpoint))

                self.lsock = lsock
                self.poller.set_readable(self)
                self.parent.started_listening(self)
                return

            except socket.error, exception:
                last_exception = exception

        LOG.error("* Bind %s failed: %s" % (self.endpoint, last_exception))
        self.parent.bind_failed(self, last_exception)

    def fileno(self):
        return self.lsock.fileno()

    def readable(self):
        try:
            sock, sockaddr = self.lsock.accept()
            sock.setblocking(False)
        except socket.error, exception:
            self.parent.accept_failed(self, exception)
            return

        self.parent.connection_made(sock)

    def closing(self, exception=None):
        LOG.error("* Bind %s failed: %s" % (self.endpoint, exception))
        self.parent.bind_failed(self, exception)     # XXX


class StreamHandler(object):

    def __init__(self, poller):
        self.poller = poller
        self.conf = {}
        self.epnts = collections.deque()
        self.bad = collections.deque()
        self.good = collections.deque()
        self.measurer = None

    def configure(self, conf, measurer=None):
        self.conf = conf
        self.measurer = measurer

    def listen(self, endpoint):
        listener = Listener(self.poller, self)
        listener.listen(endpoint, self.conf)

    def bind_failed(self, listener, exception):
        pass

    def started_listening(self, listener):
        pass

    def accept_failed(self, listener, exception):
        pass

    def connect(self, endpoint, count=1):
        while count > 0:
            self.epnts.append(endpoint)
            count = count - 1
        self._next_connect()

    def _next_connect(self):
        if self.epnts:
            connector = Connector(self.poller, self)
            connector.connect(self.epnts.popleft(), self.conf, self.measurer)
        else:
            if self.bad:
                while self.bad:
                    connector, exception = self.bad.popleft()
                    self.connection_failed(connector, exception)
                while self.good:
                    sock = self.good.popleft()
                    sock.close()
            else:
                while self.good:
                    sock = self.good.popleft()
                    self.connection_made(sock)

    def _connection_failed(self, connector, exception):
        self.bad.append((connector, exception))
        self._next_connect()

    def connection_failed(self, connector, exception):
        pass

    def started_connecting(self, connector):
        pass

    def _connection_made(self, sock):
        self.good.append(sock)
        self._next_connect()

    def connection_made(self, sock):
        pass

    def connection_lost(self, stream):
        pass


CONFIG.register_defaults({
    "net.stream.certfile": "",
    "net.stream.ipv6": False,
    "net.stream.key": "",
    "net.stream.obfuscate": False,
    "net.stream.secure": False,
    "net.stream.server_side": False,
    "net.stream.rcvbuf": 262144,
    "net.stream.sndbuf": 0,
})
CONFIG.register_descriptions({
    "net.stream.certfile": "Set SSL certfile path",
    "net.stream.ipv6": "Enable IPv6",
    "net.stream.key": "Set key for ARC4",
    "net.stream.obfuscate": "Enable scrambling with ARC4",
    "net.stream.secure": "Enable SSL",
    "net.stream.server_side": "Enable SSL server-side mode",
    "net.stream.rcvbuf": "Set sock recv buffer (0 = use default)",
    "net.stream.sndbuf": "Set sock send buffer (0 = use default)",
})


class GenericHandler(StreamHandler):

    def connection_made(self, sock):
        stream = GenericProtocolStream(self.poller)
        stream.kind = self.conf.get("net.stream.proto", "")
        stream.attach(self, sock, self.conf)


class GenericProtocolStream(Stream):

    """Specializes stream in order to handle some byte-oriented
       protocols like discard, chargen, and echo."""

    def __init__(self, poller):
        Stream.__init__(self, poller)
        self.buffer = None
        self.kind = ""

    def connection_made(self):
        self.buffer = "A" * self.conf.get("net.stream.chunk", 32768)
        MEASURER.register_stream(self)
        duration = self.conf.get("net.stream.duration", 10)
        if duration >= 0:
            POLLER.sched(duration, self.shutdown)
        if self.kind == "discard":
            self.start_recv()
        elif self.kind == "chargen":
            self.start_send(self.buffer)
        elif self.kind == "echo":
            self.start_recv()
        else:
            self.shutdown()

    def recv_complete(self, octets):
        self.start_recv()
        if self.kind == "echo":
            self.start_send(octets)

    def send_complete(self):
        if self.kind == "echo":
            self.start_recv()
            return
        self.start_send(self.buffer)


def main(args):

    CONFIG.register_defaults({
        "net.stream.address": "",
        "net.stream.chunk": 32768,
        "net.stream.clients": 1,
        "net.stream.daemonize": False,
        "net.stream.duration": 10,
        "net.stream.listen": False,
        "net.stream.port": 12345,
        "net.stream.proto": "",
    })
    CONFIG.register_descriptions({
        "net.stream.address": "Set client or server address",
        "net.stream.chunk": "Chunk written by each write",
        "net.stream.clients": "Set number of client connections",
        "net.stream.daemonize": "Enable daemon behavior",
        "net.stream.duration": "Set duration of a test",
        "net.stream.listen": "Enable server mode",
        "net.stream.port": "Set client or server port",
        "net.stream.proto": "Set proto (chargen, discard, or echo)",
    })

    boot.common("net.stream", "TCP bulk transfer test", args)

    conf = CONFIG.select("net.stream")

    if not conf["net.stream.address"]:
        if not conf["net.stream.listen"]:
            conf["net.stream.address"] = "neubot.blupixel.net"
        else:
            conf["net.stream.address"] = "0.0.0.0"

    if not (conf["net.stream.listen"] and conf["net.stream.daemonize"]):
        MEASURER.start()

    endpoint = (conf["net.stream.address"], conf["net.stream.port"])

    if not conf["net.stream.proto"]:
        if conf["net.stream.listen"]:
            conf["net.stream.proto"] = "chargen"
        else:
            conf["net.stream.proto"] = "discard"
    elif conf["net.stream.proto"] not in ("chargen", "discard", "echo"):
        boot.write_help(sys.stderr, "net.stream", "TCP bulk transfer test")
        sys.exit(1)

    handler = GenericHandler(POLLER)
    handler.configure(conf, MEASURER)

    if conf["net.stream.listen"]:
        if conf["net.stream.daemonize"]:
            system.change_dir()
            system.go_background()
            LOG.redirect()
        system.drop_privileges()
        conf["net.stream.server_side"] = True
        handler.listen(endpoint)
        POLLER.loop()
        sys.exit(0)

    handler.connect(endpoint, count=conf["net.stream.clients"])
    POLLER.loop()
    sys.exit(0)

if __name__ == "__main__":
    main(sys.argv)
