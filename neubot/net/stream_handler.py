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

""" Stream handler class """

from ..utils import utils_net

from .listener import Listener

class StreamHandler(object):
    """ Handle many streams at once """

    def __init__(self, poller):
        self.poller = poller
        self.conf = {}

    def configure(self, conf):
        """ Configure this object """
        self.conf = conf

    def listen(self, endpoint):
        """ Listen to the specified endpoint """
        sockets = utils_net.listen(endpoint)
        if not sockets:
            self.bind_failed(endpoint)
            return
        for sock in sockets:
            listener = Listener(self.poller, self, sock, endpoint)
            listener.listen()

    def bind_failed(self, epnt):
        """ Called when bind() failed """

    def started_listening(self, listener):
        """ Called when we started listening """

    def accept_failed(self, listener, exception):
        """ Called when accept fails """

    @staticmethod
    def connect(endpoint, count=1):
        """ Connect to the remote endpoint """
        raise RuntimeError

    def connection_failed(self, connector, exception):
        """ Called when a connect attempt failed """

    def started_connecting(self, connector):
        """ Called when connection is in progress """

    def connection_made(self, sock, endpoint, rtt):
        """ Called when a connection attempt succeeded """

    def connection_lost(self, stream):
        """ Called when a connection is lost """
