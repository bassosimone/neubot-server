# mod_speedtest/neubot_module.py

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

""" The entry point of the Speedtest module """

import logging
from ..runtime.poller import POLLER
from . import wrapper
from .negotiate_server_speedtest import NEGOTIATE_SERVER_SPEEDTEST
from ..negotiate_server import NEGOTIATE_SERVER


def _run_test(message):
    """ Run the Speedtest test """
    raise RuntimeError("Not implemented")

def mod_load(context, message):
    """ Invoked when the module loads """
    logging.debug("speedtest: init for context '%s'... in progress", context)

    if context == "server":
        negotiate_server = message["negotiate_server"]
        http_server = message["http_server"]

        logging.debug("speedtest: register negotiate server module... in progress")
        NEGOTIATE_SERVER.register_module('speedtest', NEGOTIATE_SERVER_SPEEDTEST)
        logging.debug("speedtest: register negotiate server module... complete")

        conf = message["configuration"]
        wrapper.run(POLLER, conf)

    else:
        logging.warning("dash: unknown context: %s", context)
    logging.debug("speedtest: init for context '%s'... complete", context)
