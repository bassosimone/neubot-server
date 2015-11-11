# mod_raw_test/neubot_module.py

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

""" The entry point of the Raw Test module """

import logging
from ..mod_raw_test.raw_srvr_glue import RAW_SERVER_EX
from .negotiate_server_raw import NEGOTIATE_SERVER_RAW
from ..negotiate_server import NEGOTIATE_SERVER

def _run_test(message):
    """ Run the Raw Test test """
    raise RuntimeError("Not implemented")

def mod_load(context, message):
    """ Invoked when the module loads """
    logging.debug("raw_test: init for context '%s'... in progress", context)

    if context == "server":
        negotiate_server = message["negotiate_server"]
        http_server = message["http_server"]

        logging.debug("raw_test: register negotiate server module... in progress")
        NEGOTIATE_SERVER.register_module('raw', NEGOTIATE_SERVER_RAW)
        logging.debug("raw_test: register negotiate server module... complete")

        conf = message["configuration"]
        RAW_SERVER_EX.listen((conf["address"], 12345), conf['prefer_ipv6'], 0, '')
        logging.debug('server: starting raw server... complete')

    else:
        logging.warning("raw_test: unknown context: %s", context)

    logging.debug("raw_test: init for context '%s'... complete", context)
