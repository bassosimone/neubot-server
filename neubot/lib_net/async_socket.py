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

""" Async socket """

import errno
import logging
import socket

from .pollable import SUCCESS
from .pollable import WANT_READ
from .pollable import WANT_WRITE
from .pollable import CONNRST

# Soft errors on sockets, i.e. we can retry later
SOFT_ERRORS = (errno.EAGAIN, errno.EWOULDBLOCK, errno.EINTR)

class AsyncSocket(object):
    """ Async socket """

    def __init__(self, sock):
        self._sock = sock

    def soclose(self):
        """ Close this socket """
        try:
            self._sock.close()
        except socket.error:
            logging.error('Exception', exc_info=1)

    def sorecv(self, maxlen):
        """ Receive from this socket """
        try:
            octets = self._sock.recv(maxlen)
            return SUCCESS, octets
        except socket.error as exception:
            if exception[0] in SOFT_ERRORS:
                return WANT_READ, b""
            elif exception[0] == errno.ECONNRESET:
                return CONNRST, b""
            else:
                raise

    def sosend(self, octets):
        """ Send on this socket """
        try:
            count = self._sock.send(octets)
            return SUCCESS, count
        except socket.error as exception:
            if exception[0] in SOFT_ERRORS:
                return WANT_WRITE, 0
            elif exception[0] == errno.ECONNRESET:
                return CONNRST, 0
            else:
                raise
