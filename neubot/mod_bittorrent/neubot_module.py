# mod_bittorrent/neubot_module.py

#
# Copyright (c) 2013
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

""" The entry point of the Bittorrent module """

import logging
from ..runtime.poller import POLLER
from .. import mod_bittorrent
from .negotiate_server_bittorrent import NEGOTIATE_SERVER_BITTORRENT
from ..negotiate_server import NEGOTIATE_SERVER

def _run_test(message):
    """ Run the Bittorrent test """
    raise RuntimeError("Not implemented")

def mod_load(context, message):
    """ Invoked when the module loads """
    logging.debug("bittorrent: init for context '%s'... in progress", context)

    if context == "server":
        negotiate_server = message["negotiate_server"]
        http_server = message["http_server"]

        logging.debug("bittorrent: register negotiate server module... in progress")
        NEGOTIATE_SERVER.register_module('bittorrent', NEGOTIATE_SERVER_BITTORRENT)
        logging.debug("bittorrent: register negotiate server module... complete")

        conf = message["configuration"]
        conf["bittorrent.address"] = conf["address"]
        conf["bittorrent.listen"] = True
        conf["bittorrent.negotiate"] = True
        mod_bittorrent.run(POLLER, conf)

    else:
        logging.warning("bittorrent: unknown context: %s", context)

    logging.debug("bittorrent: init for context '%s'... complete", context)
