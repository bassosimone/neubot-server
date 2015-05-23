#
# Copyright (c) 2010, 2012, 2015
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

''' An object that can be passed to the poller '''

from .. import utils

# States returned by the socket model
(SUCCESS, WANT_READ, WANT_WRITE, CONNRST) = range(4)

# Reclaim stream after 300 seconds
WATCHDOG = 300

class Pollable(object):
    ''' Base class for pollable objects '''

    def __init__(self):
        self._created = utils.ticks()
        self._watchdog = WATCHDOG

    def fileno(self):
        ''' Return file descriptor number '''

    def handle_read(self):
        ''' Handle the READ event '''

    def handle_write(self):
        ''' Handle the WRITE event '''

    def handle_close(self):
        ''' Handle the CLOSE event '''

    def handle_periodic(self, timenow):
        ''' Handle the PERIODIC event '''
        return self._watchdog >= 0 and timenow - self._created > self._watchdog

    def set_timeout(self, timeo):
        ''' Set timeout of this pollable '''
        self._created = utils.ticks()
        self._watchdog = timeo
