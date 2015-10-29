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

""" Server-side API """

from .lib_http.message import Message
from .lib_http.server import ServerHTTP

from .negotiate.server import NEGOTIATE_SERVER

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
