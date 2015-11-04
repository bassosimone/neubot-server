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

''' HTTP client '''

import logging

from .stream_handler import StreamHandler
from .http_client_stream import HttpClientStream
from .http_message import HttpMessage
from . import utils
from . import utils_net

class HttpClient(StreamHandler):

    ''' Manages one or more HTTP streams '''

    def __init__(self, poller):
        ''' Initialize the HTTP client '''
        StreamHandler.__init__(self, poller)
        self.host_header = ""
        self.rtt = 0

    def connect_uri(self, uri, count=1):
        ''' Connects to the given URI '''
        try:
            message = HttpMessage()
            message.compose(method="GET", uri=uri)
            if message.scheme == "https":
                self.conf["net.stream.secure"] = True
            endpoint = (message.address, int(message.port))
            self.host_header = utils_net.format_epnt(endpoint)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as why:
            self.connection_failed(None, why)
        else:
            self.connect(endpoint, count)

    def connection_ready(self, stream):
        ''' Invoked when the connection is ready '''

    def got_response_headers(self, stream, request, response):
        ''' Invoked when we receive response headers '''
        return True

    def got_response(self, stream, request, response):
        ''' Invoked when we receive the response '''

    def connection_made(self, sock, endpoint, rtt):
        ''' Invoked when the connection is created '''
        if rtt:
            logging.debug("ClientHTTP: latency: %s", utils.time_formatter(rtt))
            self.rtt = rtt
        # XXX If we didn't connect via connect_uri()...
        if not self.host_header:
            self.host_header = utils_net.format_epnt(endpoint)
        stream = HttpClientStream(self.poller)
        stream.attach(self, sock, self.conf)
        self.connection_ready(stream)
