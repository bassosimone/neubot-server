# neubot/net/stream.py

#
# There are tons of pylint warnings in this file, disable
# the less relevant ones for now.
#
# pylint: disable=C0111
#

#
# Copyright (c) 2010-2012 Simone Basso <bassosimone@gmail.com>,
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
import types
import logging

from ..log import oops
from .pollable import Pollable
from .pollable import SUCCESS
from .pollable import WANT_READ
from .pollable import WANT_WRITE
from .pollable import CONNRST
from .async_socket import AsyncSocket

from ..utils import utils_net

# Maximum amount of bytes we read from a socket
MAXBUF = 1 << 18

class Stream(Pollable):
    def __init__(self, poller):
        Pollable.__init__(self)
        self.poller = poller
        self.parent = None
        self.conf = None

        self.sock = None
        self.filenum = -1
        self.myname = None
        self.peername = None
        self.logname = None
        self.eof = False
        self.rst = False

        self.close_complete = False
        self.close_pending = False
        self.recv_pending = False
        self.send_octets = None
        self.send_queue = collections.deque()
        self.send_pending = False

        self.bytes_recv_tot = 0
        self.bytes_sent_tot = 0

        self.opaque = None
        self.atclosev = set()

    def __repr__(self):
        return "stream %s" % self.logname

    def fileno(self):
        return self.filenum

    def attach(self, parent, sock, conf):

        self.parent = parent
        self.conf = conf

        self.filenum = sock.fileno()
        self.myname = utils_net.getsockname(sock)
        self.peername = utils_net.getpeername(sock)
        self.logname = str((self.myname, self.peername))

        logging.debug("* Connection made %s", str(self.logname))

        self.sock = AsyncSocket(sock)

        self.connection_made()

    def connection_made(self):
        pass

    def atclose(self, func):
        if func in self.atclosev:
            oops("Duplicate atclose(): %s" % func)
        self.atclosev.add(func)

    def unregister_atclose(self, func):
        if func in self.atclosev:
            self.atclosev.remove(func)

    # Close path

    def connection_lost(self, exception):
        pass

    def close(self):
        self.close_pending = True
        if self.send_pending or self.close_complete:
            return
        self.poller.close(self)

    def handle_close(self):
        if self.close_complete:
            return

        self.close_complete = True

        self.connection_lost(None)
        self.parent.connection_lost(self)

        atclosev, self.atclosev = self.atclosev, set()
        for func in atclosev:
            try:
                func(self, None)
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                logging.error("Error in atclosev", exc_info=1)

        self.send_octets = None
        self.sock.soclose()

    # Recv path

    def start_recv(self):
        if (self.close_complete or self.close_pending
                or self.recv_pending):
            return

        self.recv_pending = True
        self.poller.set_readable(self)

    def handle_read(self):
        status, octets = self.sock.sorecv(MAXBUF)

        if status == SUCCESS and octets:

            self.bytes_recv_tot += len(octets)
            self.recv_pending = False
            self.poller.unset_readable(self)

            self.recv_complete(octets)
            return

        if status == WANT_READ:
            return

        if status == CONNRST and not octets:
            self.rst = True
            self.poller.close(self)
            return

        if status == SUCCESS and not octets:
            self.eof = True
            self.poller.close(self)
            return

        raise RuntimeError("Unexpected status value")

    def recv_complete(self, octets):
        pass

    # Send path

    def read_send_queue(self):
        octets = ""

        while self.send_queue:
            octets = self.send_queue[0]
            if isinstance(octets, basestring):
                # remove the piece in any case
                self.send_queue.popleft()
                if octets:
                    break
            else:
                octets = octets.read(MAXBUF)
                if octets:
                    break
                # remove the file-like when it is empty
                self.send_queue.popleft()

        if octets:
            if type(octets) == types.UnicodeType:
                oops("Received unicode input")
                octets = octets.encode("utf-8")

        return octets

    def start_send(self, octets):
        if self.close_complete or self.close_pending:
            return

        self.send_queue.append(octets)
        if self.send_pending:
            return

        self.send_octets = self.read_send_queue()
        if not self.send_octets:
            return

        self.send_pending = True
        self.poller.set_writable(self)

    def handle_write(self):
        status, count = self.sock.sosend(self.send_octets)

        if status == SUCCESS and count > 0:
            self.bytes_sent_tot += count

            if count == len(self.send_octets):

                self.send_octets = self.read_send_queue()
                if self.send_octets:
                    return

                self.send_pending = False
                self.poller.unset_writable(self)

                self.send_complete()
                if self.close_pending:
                    self.poller.close(self)
                return

            if count < len(self.send_octets):
                self.send_octets = buffer(self.send_octets, count)
                self.poller.set_writable(self)
                return

            raise RuntimeError("Sent more than expected")

        if status == WANT_WRITE:
            return

        if status == CONNRST and count == 0:
            self.rst = True
            self.poller.close(self)
            return

        if status == SUCCESS and count == 0:
            self.eof = True
            self.poller.close(self)
            return

        if status == SUCCESS and count < 0:
            raise RuntimeError("Unexpected count value")

        raise RuntimeError("Unexpected status value")

    def send_complete(self):
        pass
