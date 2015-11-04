#
# Copyright (c) 2010-2012, 2015
#     Nexa Center for Internet & Society, Politecnico di Torino (DAUIN)
#     and Simone Basso <bassosimone@gmail.com>.
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

""" Internally used connector """

import collections
import logging

from .pollable import Pollable
from . import utils
from . import utils_net

class Connector(Pollable):
    """ Connects to the remote endpoint """

    def __init__(self, poller, parent):
        Pollable.__init__(self)
        self.conf = {}
        self.poller = poller
        self.parent = parent
        self.sock = None
        self.timestamp = 0
        self.endpoint = None
        self.epnts = collections.deque()
        self.watchdog = 10

    def __repr__(self):
        return "connector to %s" % str(self.endpoint)

    def _connection_failed(self):
        """ Internally called when connection fails """
        if self.sock:
            self.poller.unset_writable(self)
            self.sock = None
        if not self.epnts:
            self.parent.connection_failed(self, None)
            return
        self.connect(self.epnts.popleft(), self.conf)

    def connect(self, endpoint, conf):
        """ Connect to the remote endpoint """

        # Connect first address in a list
        if ' ' in endpoint[0]:
            logging.debug('connecting to %s', str(endpoint))
            for address in endpoint[0].split():
                epnt = (address.strip(), endpoint[1])
                self.epnts.append(epnt)
            endpoint = self.epnts.popleft()

        self.endpoint = endpoint
        self.conf = conf

        sock = utils_net.connect(endpoint, conf.get("prefer_ipv6", False))
        if not sock:
            self._connection_failed()
            return

        self.sock = sock
        self.timestamp = utils.ticks()
        self.poller.set_writable(self)

    def fileno(self):
        return self.sock.fileno()

    def handle_write(self):
        self.poller.unset_writable(self)

        if not utils_net.isconnected(self.endpoint, self.sock):
            self._connection_failed()
            return

        rtt = utils.ticks() - self.timestamp
        self.parent.connection_made(self.sock, self.endpoint, rtt)

    def handle_close(self):
        self._connection_failed()
