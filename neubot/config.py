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
# =================================================================
# The update() method of ConfigDict is a derivative work
# of Python 2.5.2 Object/dictobject.c dict_update_common().
#
# Copyright (c) 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008
# Python Software Foundation; All Rights Reserved.
#
# I've put a copy of Python LICENSE file at doc/LICENSE.Python.
# =================================================================
#

import itertools
import os
import shlex
import logging

from neubot import utils

def string_to_kv(string):

    """Convert string to (key,value).  Returns the empty tuple if
       the string is a comment or contains just spaces."""

    string = string.strip()
    if not string or string[0] == "#":
        return tuple()
    kv = string.split("=", 1)
    if len(kv) == 1:
        kv.append("True")
    return tuple(kv)

def kv_to_string(kv):

    """Convert (key,value) to string.  Adds a trailing newline so
       we can pass the return value directly to fp.write()."""

    return "%s=%s\n" % (utils.stringify(kv[0]), utils.stringify(kv[1]))

class ConfigDict(dict):

    """Modified dictionary.  At the beginning we fill it with default
       values, e.g. when a new module is loaded.  Then, when we update
       this dictionary we want new values to have the same type of the
       old ones.  We perform the check when the dictionary is updated
       and not when it is accessed because in the latter case we might
       delay errors and that would be surprising."""

    def __setitem__(self, key, value):
        if key in self:
            ovalue = self[key]
            cast = utils.smart_cast(ovalue)
        else:
            ovalue = "(none)"
            cast = utils.smart_cast(value)
        value = cast(value)
        logging.debug("config: %s: %s -> %s", key, ovalue, value)
        dict.__setitem__(self, key, value)

    def update(self, *args, **kwds):
        if args:
            arg = tuple(args)[0]
            if hasattr(arg, "keys"):
                arg = arg.iteritems()
            map(lambda t: self.__setitem__(t[0], t[1]), arg)
        if kwds:
            self.update(kwds.iteritems())

class ConfigError(Exception):
    pass

class Config(object):

    """Configuration manager"""

    def __init__(self):
        self.properties = []
        self.conf = ConfigDict()
        self.descriptions = {}

    def register_defaults(self, kvstore):
        self.conf.update(kvstore)

    def register_descriptions(self, d):
        self.descriptions.update(d)

    def copy(self):
        return dict(self.conf)

    def get(self, key, defvalue):
        return self.conf.get(key, defvalue)

    def __getitem__(self, key):
        return self.conf[key]

    def __setitem__(self, key, value):
        self.conf[key] = value

    def register_property(self, prop, module=""):
        if module and not prop.startswith(module):
            prop = "%s.%s" % (module, prop)
        self.properties.append(prop)

    def merge_fp(self, fp):
        logging.debug("config: reading properties from file")
        map(self.merge_kv, itertools.imap(string_to_kv, fp))

    def merge_database(self, database):
        logging.debug("config: reading properties from database")

    def merge_environ(self):
        logging.debug("config: reading properties from the environment")
        map(self.merge_kv, itertools.imap(string_to_kv,
          shlex.split(os.environ.get("NEUBOT_OPTIONS",""))))

    def merge_properties(self):
        logging.debug("config: reading properties from command-line")
        map(self.merge_kv, itertools.imap(string_to_kv, self.properties))

    def merge_api(self, dictlike, database=None):
        # enforce all-or-nothing
        logging.debug("config: reading properties from /api/config")
        map(lambda t: self.merge_kv(t, dry=True), dictlike.iteritems())
        map(self.merge_kv, dictlike.iteritems())

    def merge_kv(self, t, dry=False):
        if t:
            key, value = t
            if not dry:
                self.conf[key] = value

            else:
                try:
                    ovalue = self.conf[key]
                    cast = utils.smart_cast(ovalue)
                    cast(value)
                except KeyError:
                    raise ConfigError("No such property: %s" % key)
                except TypeError:
                    raise ConfigError("Old value '%s' for property '%s'"
                      " has the wrong type" % (ovalue, key))
                except ValueError:
                    raise ConfigError("Invalid value '%s' for property '%s'" %
                                      (value, key))

    def store_fp(self, fp):
        map(fp.write, itertools.imap(kv_to_string, self.conf.iteritems()))

    def store_database(self, database):
        pass

    def print_descriptions(self, fp):
        fp.write("Properties (current value in square brackets):\n")
        for key in sorted(self.descriptions.keys()):
            description = self.descriptions[key]
            value = self.conf[key]
            fp.write("    %-28s: %s [%s]\n" % (key, description, value))
        fp.write("\n")

CONFIG = Config()

CONFIG.register_defaults_helper = lambda properties: \
    CONFIG.register_defaults(dict(zip(map(lambda t: t[0], properties),
                                      map(lambda t: t[1], properties))))

CONFIG.register_descriptions_helper = lambda properties: \
    CONFIG.register_descriptions(dict(zip(map(lambda t: t[0], properties),
                                          map(lambda t: t[2], properties))))

CONFIG.register_defaults({
    "prefer_ipv6": 0,
})

CONFIG.register_descriptions({
    "prefer_ipv6": "Prefer IPv6 over IPv4 when resolving domain names",
})
