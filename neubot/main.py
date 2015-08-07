#
# Copyright (c) 2011-2012, 2015
#    Nexa Center for Internet & Society, Politecnico di Torino (DAUIN)
#    and Simone Basso <bassosimone@gmail.com>.
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

""" Neubot server """

import getopt
import sys
import logging
import os
import signal

if __name__ == "__main__":
    sys.path.insert(0, ".")

from .lib_http.message import Message
from .lib_http.server import HTTP_SERVER
from .lib_http.server import ServerHTTP
from .lib_net.poller import POLLER

from .negotiate.server import NEGOTIATE_SERVER

from .config import CONFIG
from .mod_raw_test.raw_srvr_glue import RAW_SERVER_EX

from . import backend
from . import log
from . import mod_bittorrent
from . import negotiate
from .utils import utils_modules
from .utils import utils_posix

#from . import speedtest           # Not yet
import neubot.mod_speedtest.wrapper

from .utils.utils_hier import LOCALSTATEDIR


class ServerSideAPI(ServerHTTP):
    """ Implements server-side API for Nagios plugin """

    def process_request(self, stream, request):
        """ Process HTTP request and return response """

        if request.uri == "/sapi":
            request.uri = "/sapi/"

        response = Message()

        if request.uri == "/sapi/":
            body = '["/sapi/", "/sapi/state"]'
            response.compose(code="200", reason="Ok", body=body,
                             mimetype="application/json")
        elif request.uri == "/sapi/state":
            body = '{"queue_len_cur": %d}' % len(NEGOTIATE_SERVER.queue)
            response.compose(code="200", reason="Ok", body=body,
                             mimetype="application/json")
        else:
            response.compose(code="404", reason="Not Found")

        stream.send_response(request, response)

SETTINGS = {
    "server.bittorrent": True,
    "server.daemonize": True,
    "server.datadir": LOCALSTATEDIR,
    "server.negotiate": True,
    "server.raw": True,
    "server.sapi": True,
    "server.speedtest": True,
}

USAGE = '''\
usage: neubot server [-dv] [-A address] [-b backend] [-D macro=value]

valid backends:
  mlab   Saves results as compressed json files (this is the default)
  neubot Saves results in sqlite3 database
  null   Do not save results but pretend to do so

valid defines:
  server.bittorrent Set to nonzero to enable BitTorrent server (default: 1)
  server.daemonize  Set to nonzero to run in the background (default: 1)
  server.datadir    Set data directory (default: LOCALSTATEDIR/neubot)
  server.negotiate  Set to nonzero to enable negotiate server (default: 1)
  server.raw        Set to nonzero to enable RAW server (default: 1)
  server.sapi       Set to nonzero to enable nagios API (default: 1)
  server.speedtest  Set to nonzero to enable speedtest server (default: 1)'''

VALID_MACROS = ('server.bittorrent', 'server.daemonize', 'server.datadir',
                'server.negotiate', 'server.raw',
                'server.sapi', 'server.speedtest')

def main(args):
    """ Starts the server module """

    if os.getuid() != 0:
        sys.exit('FATAL: you must be root')

    try:
        options, arguments = getopt.getopt(args[1:], 'A:b:D:dv')
    except getopt.error:
        sys.exit(USAGE)
    if arguments:
        sys.exit(USAGE)

    address = ':: 0.0.0.0'
    for name, value in options:
        if name == '-A':
            address = value
        elif name == '-D':
            name, value = value.split('=', 1)
            if name not in VALID_MACROS:
                sys.exit(USAGE)
            if name != 'server.datadir':  # XXX
                value = int(value)
            SETTINGS[name] = value
        elif name == '-d':
            SETTINGS['server.daemonize'] = 0
        elif name == '-v':
            log.set_verbose()

    backend.setup(CONFIG["unpriv_user"], SETTINGS['server.datadir'])

    for name, value in SETTINGS.items():
        CONFIG[name] = value

    conf = CONFIG.copy()

    #
    # Configure our global HTTP server and make
    # sure that we don't provide filesystem access
    # even by mistake.
    #
    conf["http.server.rootdir"] = ""
    HTTP_SERVER.configure(conf)

    #
    # New-new style: don't bother with abstraction and start the fucking
    # server by invoking its listen() method.
    #
    if CONFIG['server.raw']:
        logging.debug('server: starting raw server... in progress')
        RAW_SERVER_EX.listen((address, 12345),
          CONFIG['prefer_ipv6'], 0, '')
        logging.debug('server: starting raw server... complete')

    #
    # New-style modules are started just setting a
    # bunch of conf[] variables and then invoking
    # their run() method in order to kick them off.
    # This is now depricated in favor of the new-
    # new style described above.
    #

    if conf["server.negotiate"]:
        negotiate.run(POLLER, conf)

    if conf["server.bittorrent"]:
        conf["bittorrent.address"] = address
        conf["bittorrent.listen"] = True
        conf["bittorrent.negotiate"] = True
        mod_bittorrent.run(POLLER, conf)

    if conf['server.speedtest']:
        #conf['speedtest.listen'] = 1           # Not yet
        #conf['speedtest.negotiate'] = 1        # Not yet
        neubot.mod_speedtest.wrapper.run(POLLER, conf)

    #
    # Historically Neubot runs on port 9773 and
    # 8080 but we would like to switch to port 80
    # in the long term period, because it's rare
    # that they filter it.
    # OTOH it looks like it's not possible to
    # do that easily w/ M-Lab because the port
    # is already taken.
    #
    ports = (80, 8080, 9773)
    for port in ports:
        HTTP_SERVER.listen((address, port))

    #
    # Start server-side API for Nagios plugin
    # to query the state of the server.
    # functionalities.
    #
    if conf["server.sapi"]:
        server = ServerSideAPI(POLLER)
        server.configure(conf)
        HTTP_SERVER.register_child(server, "/sapi")

    # Probe existing modules and ask them to attach to us
    utils_modules.modprobe(None, "server", {
        "http_server": HTTP_SERVER,
        "negotiate_server": NEGOTIATE_SERVER,
    })

    #
    # Go background and drop privileges,
    # then enter into the main loop.
    #
    if conf["server.daemonize"]:
        log.redirect()
        utils_posix.daemonize(pidfile='/var/run/neubot.pid')

    sigterm_handler = lambda signo, frame: POLLER.break_loop()
    signal.signal(signal.SIGTERM, sigterm_handler)

    logging.info('Neubot server -- starting up')
    utils_posix.chuser(utils_posix.getpwnam(CONFIG["unpriv_user"]))
    POLLER.loop()

    logging.info('Neubot server -- shutting down')
    utils_posix.remove_pidfile('/var/run/neubot.pid')

if __name__ == "__main__":
    main(sys.argv)
