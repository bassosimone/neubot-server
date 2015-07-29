# neubot/raw.py

#
# Copyright (c) 2012
#     Nexa Center for Internet & Society, Politecnico di Torino (DAUIN)
#     and Simone Basso <bassosimone@gmail.com>
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

'''
 The main() of `neubot raw` subcommand.
'''

import getopt
import logging
import os
import sys

if __name__ == '__main__':
    sys.path.insert(0, '.')

from .lib_net.poller import POLLER

from . import log
from . import privacy

def main(args):
    ''' Main function '''
    try:
        options, arguments = getopt.getopt(args[1:], '6A:fp:v')
    except getopt.error:
        sys.exit('usage: neubot raw [-6fv] [-A address] [-p port]')
    if arguments:
        sys.exit('usage: neubot raw [-6fv] [-A address] [-p port]')

    prefer_ipv6 = 0
    address = 'master.neubot.org'
    force = 0
    port = 8080
    noisy = 0
    for name, value in options:
        if name == '-6':
            prefer_ipv6 = 1
        elif name == '-A':
            address = value
        elif name == '-f':
            force = 1
        elif name == '-p':
            port = int(value)
        elif name == '-v':
            noisy = 1

    if noisy:
        log.set_verbose()

    if not force:
        logging.warning('raw: failed to contact Neubot; is Neubot running?')
        sys.exit(1)

    raise RuntimeError("raw: client mode not implemented")

if __name__ == '__main__':
    main(sys.argv)
