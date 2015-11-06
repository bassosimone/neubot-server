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

import collections

from .http_stream import HttpStream
from .http_stream import ERROR
from .http_misc import nextstate
from .http_message import HttpMessage
from . import utils

class HttpClientStream(HttpStream):

    ''' Specializes HttpStream and implements the client
        side of an HTTP channel '''

    def __init__(self, poller):
        ''' Initialize client stream '''
        HttpStream.__init__(self, poller)
        self.requests = collections.deque()

    def send_request(self, request, response=None):
        ''' Sends a request '''
        self.requests.append(request)
        if not response:
            response = HttpMessage()
        request.response = response
        self.send_message(request)

    def got_response_line(self, protocol, code, reason):
        ''' Invoked when we receive the response line '''
        if self.requests:
            response = self.requests[0].response
            response.protocol = protocol
            response.code = code
            response.reason = reason
        else:
            self.close()

    def got_header(self, key, value):
        ''' Invoked when we receive an header '''
        if self.requests:
            response = self.requests[0].response
            response[key] = value
        else:
            self.close()

    def got_end_of_headers(self):
        ''' Invoked at the end of headers '''
        if self.requests:
            request = self.requests[0]
            if not self.parent.got_response_headers(self, request,
                                                    request.response):
                return ERROR, 0
            return nextstate(request, request.response)
        else:
            return ERROR, 0

    def got_piece(self, piece):
        ''' Invoked when we receive a body piece '''
        if self.requests:
            response = self.requests[0].response
            response.body.write(piece)
        else:
            self.close()

    def got_end_of_body(self):
        ''' Invoked at the end of the body '''
        if self.requests:
            request = self.requests.popleft()
            utils.safe_seek(request.response.body, 0)
            request.response.prettyprintbody("<")
            self.parent.got_response(self, request, request.response)
            if (request["connection"] == "close" or
                    request.response["connection"] == "close"):
                self.close()
        else:
            self.close()
