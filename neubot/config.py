# neubot/config.py

#
# Copyright (c) 2010-2011, 2013
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

import logging

from neubot import utils

class Config(object):

    """Configuration manager"""

    def __init__(self):
        self.conf = {}

    def register_defaults(self, kvstore):
        self.conf.update(kvstore)

    def copy(self):
        return dict(self.conf)

    def get(self, key, defvalue):
        return self.conf.get(key, defvalue)

    def __getitem__(self, key):
        return self.conf[key]

    def __setitem__(self, key, value):
        self.conf[key] = value

CONFIG = Config()

CONFIG.register_defaults_helper = lambda properties: \
    CONFIG.register_defaults(dict(zip(map(lambda t: t[0], properties),
                                      map(lambda t: t[1], properties))))

CONFIG.register_defaults({
    "prefer_ipv6": 0,
})
