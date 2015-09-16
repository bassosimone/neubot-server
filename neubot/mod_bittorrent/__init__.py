# neubot.mod_bittorrent/__init__.py

#
# Copyright (c) 2011 Simone Basso <bassosimone@gmail.com>,
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

'''
 This file contains the external entry points to
 the bittorrent module, that tries to emulate the
 behavior of a bittorrent peer.
'''

import getopt
import logging
import os
import sys

if __name__ == "__main__":
    sys.path.insert(0, ".")

from .peer import PeerNeubot
from .server import ServerPeer
from ..lib_http.server import HTTP_SERVER
from ..lib_net.poller import POLLER

from .. import config
from ..config import CONFIG

from .. import log
from .. import negotiate
from .. import utils

def run(poller, conf):
    '''
     This function is invoked when Neubot is already
     running and you want to leverage some functionalities
     of this module.
    '''

    # Make sure the conf makes sense before we go
    config.finalize_conf(conf)

    if conf["bittorrent.listen"]:
        if conf["bittorrent.negotiate"]:

            #
            # We assume that the caller has already started
            # the HTTP server and that it contains our negotiator
            # so here we just bring up the test server.
            #
            server = ServerPeer(poller)
            server.configure(conf)
            server.listen((conf["bittorrent.address"],
                           conf["bittorrent.port"]))

        else:
            server = PeerNeubot(poller)
            server.configure(conf)
            server.listen((conf["bittorrent.address"],
                           conf["bittorrent.port"]))

    else:

        raise RuntimeError("BitTorrent client not implemented")

def main(args):
    '''
     This function is invoked when the user wants
     to run precisely this module.
    '''

    try:
        options, arguments = getopt.getopt(args[1:], '6A:fp:v')
    except getopt.error:
        sys.exit('usage: neubot.mod_bittorrent [-6fv] [-A address] [-p port]')
    if arguments:
        sys.exit('usage: neubot.mod_bittorrent [-6fv] [-A address] [-p port]')

    prefer_ipv6 = 0
    address = 'master.neubot.org'
    force = 0
    port = 6881
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

    conf = CONFIG.copy()
    config.finalize_conf(conf)

    conf['bittorrent.address'] = address
    conf['bittorrent.port'] = port
    conf['prefer_ipv6'] = prefer_ipv6

    if not force:
        logging.warning(
          'bittorrent: failed to contact Neubot; is Neubot running?')
        sys.exit(1)

    logging.info('bittorrent: run the test in the local process context...')
    raise RuntimeError("Not implemented")

if __name__ == "__main__":
    main(sys.argv)
