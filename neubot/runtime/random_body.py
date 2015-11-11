#
# Copyright (c) 2011, 2015
#     Nexa Center for Internet & Society, Politecnico di Torino (DAUIN)
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

''' Random body for HTTP code '''

class RandomBody(object):

    '''
     This class implements a minimal file-like interface and
     employs the random number generator to create the content
     returned by its read() method.
    '''

    def __init__(self, random_blocks, total):
        ''' Initialize random body object '''
        self._random_blocks = random_blocks
        self._total = total

    def read(self, want=None):
        ''' Read up to @want bytes '''
        if not want:
            want = self._total
        amt = min(self._total, min(want, self._random_blocks.blocksiz))
        if amt:
            self._total -= amt
            return self._random_blocks.get_block()[:amt]
        else:
            return b''

    def seek(self, offset=0, whence=0):
        ''' Seek stub '''

    def tell(self):
        ''' Tell the amounts of bytes left '''
        return self._total
