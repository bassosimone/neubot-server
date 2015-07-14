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

""" Internally used listener """

from .pollable import Pollable

class Listener(Pollable):
    """ Listen to a specific endpoint """

    def __init__(self, poller, parent, sock, endpoint):
        Pollable.__init__(self)
        self._poller = poller
        self._parent = parent
        self._sock = sock
        self._endpoint = endpoint

        # Want to listen "forever"
        self.set_timeout(-1)

    def __repr__(self):
        return "listener at %s" % str(self._endpoint)

    def listen(self):
        """ Actually start listening """
        self._poller.set_readable(self)
        self._parent.started_listening(self)

    def fileno(self):
        return self._sock.fileno()

    #
    # Catch all types of exception because an error in
    # connection_made() MUST NOT cause the server to stop
    # listening for new connections.
    #
    def handle_read(self):
        try:
            sock = self._sock.accept()[0]
            sock.setblocking(False)
            self._parent.connection_made(sock, self._endpoint, 0)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception, exception:
            self._parent.accept_failed(self, exception)
            return

    def handle_close(self):
        self._parent.bind_failed(self._endpoint)  # XXX
