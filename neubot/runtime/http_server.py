#
# Copyright (c) 2010-2011, 2015
#     Nexa Center for Internet & Society, Politecnico di Torino (DAUIN),
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

''' HTTP server '''

import sys
import logging

from .http_message import HttpMessage
from .http_server_stream import HttpServerStream
from .stream_handler import StreamHandler
from .poller import POLLER

class HttpServer(StreamHandler):

    ''' Manages many HTTP connections '''

    def __init__(self, poller):
        ''' Initialize the HTTP server '''
        StreamHandler.__init__(self, poller)
        self._ssl_ports = set()
        self.childs = {}

    def bind_failed(self, epnt):
        ''' Invoked when we cannot bind a socket '''
        if self.conf.get("http.server.bind_or_die", False):
            sys.exit(1)

    def register_child(self, child, prefix):
        ''' Register a child server object '''
        self.childs[prefix] = child
        child.child = self

    def register_ssl_port(self, port):
        ''' Register a port where we should speak SSL '''
        self._ssl_ports.add(port)

    def got_request_headers(self, stream, request):
        ''' Invoked when we got request headers '''
        if self.childs:
            for prefix, child in self.childs.items():
                if request.uri.startswith(prefix):
                    try:
                        return child.got_request_headers(stream, request)
                    except (KeyboardInterrupt, SystemExit):
                        raise
                    except:
                        self._on_internal_error(stream, request)
                        return False
        return True

    def process_request(self, stream, request):
        ''' Process a request and generate the response '''
        response = HttpMessage()

        if not request.uri.startswith("/"):
            response.compose(code="403", reason="Forbidden",
                             body="403 Forbidden")
            stream.send_response(request, response)
            return

        for prefix, child in self.childs.items():
            if request.uri.startswith(prefix):
                child.process_request(stream, request)
                return

        response.compose(code="403", reason="Forbidden",
                         body="403 Forbidden")
        stream.send_response(request, response)

    def got_request(self, stream, request):
        ''' Invoked when we got a request '''
        try:
            self.process_request(stream, request)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self._on_internal_error(stream, request)

    @staticmethod
    def _on_internal_error(stream, request):
        ''' Generate 500 Internal Server Error page '''
        logging.error('Internal error while serving response', exc_info=1)
        response = HttpMessage()
        response.compose(code="500", reason="Internal Server Error",
                         body="500 Internal Server Error", keepalive=0)
        stream.send_response(request, response)
        stream.close()

    def connection_made(self, sock, endpoint, rtt):
        ''' Invoked when the connection is made '''
        stream = HttpServerStream(self.poller)
        stream.attach(self, sock, self.conf.copy())
        self.connection_ready(stream)

    def connection_ready(self, stream):
        ''' Invoked when the connection is ready '''

    def accept_failed(self, listener, exception):
        ''' Print a warning if accept() fails (often due to SSL) '''
        logging.warning("HttpServer: accept() failed: %s", str(exception))

HTTP_SERVER = HttpServer(POLLER)
