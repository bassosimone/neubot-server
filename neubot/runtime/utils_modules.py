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

""" Utils for loading tests as modules """

#
# Python3-ready: yes
#

import logging
import os
import sys

from . import utils_hier

def modprobe(filt, context, message):
    """ Probe all modules """

    rootdir = utils_hier.ROOTDIR

    for name in os.listdir(rootdir):
        pathname = os.sep.join([rootdir, name])
        if not os.path.isdir(pathname):
            continue
        if not name.startswith("mod_"):
            continue

        logging.debug("utils_modules: early candidate: %s", name)

        initfile = os.sep.join([pathname, "__init__.py"])
        if not os.path.isfile(initfile):
            continue

        modfile = os.sep.join([pathname, "neubot_module.py"])
        if not os.path.isfile(modfile):
            continue

        logging.debug("utils_modules: good candidate: %s", name)

        if filt != None and name != filt:
            logging.debug("utils_modules: skip '%s' (filt: %s)", name, filt)
            continue

        modname = "%s.neubot_module" % name

        try:
            __import__(modname)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            logging.warning("utils_modules: import error for: %s",
                            name, exc_info=1)
            continue

        logging.debug("utils_modules: import '%s'... OK", name)

        try:
            mod_load = sys.modules[modname].mod_load
        except AttributeError:
            logging.warning("utils_modules: no mod_load() in '%s'", name)
            continue

        logging.debug("utils_modules: found mod_load() in '%s'", name)

        try:
            mod_load(context, message)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            logging.warning("utils_modules: mod_load() error for '%s'",
                            name, exc_info=1)
            continue

        logging.debug("utils_modules: load '%s' context '%s'", name, context)
