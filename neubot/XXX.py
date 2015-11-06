# neubot/XXX.py

#
# Copyright (c) 2010-2011 Simone Basso <bassosimone@gmail.com>,
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

''' Transition utility function file'''

import types

def stringify(value):
    ''' Convert something to string '''
    if type(value) == types.UnicodeType:
        return value.encode("utf-8")
    elif type(value) == types.StringType:
        return value
    else:
        return str(value)

def unicodize(value):
    ''' Convert something to unicode '''
    if type(value) == types.UnicodeType:
        return value
    elif type(value) == types.StringType:
        return value.decode("utf-8")
    else:
        return unicode(value)
