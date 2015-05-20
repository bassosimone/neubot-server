#
# Copyright (c) 2012-2013, 2015
#     Nexa Center for Internet & Society, Politecnico di Torino (DAUIN)
#     and Simone Basso <bassosimone@gmail.com>.
#
# Copyright (c) 2012 Fabio Forno <fabio.forno@gmail.com>
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

""" Save results to disk """

from neubot.utils import utils_path
from neubot.utils import utils_posix

import gzip
import json
import logging
import time

class Backend(object):
    """ Controls how data is saved to disk """

    _singleton = None

    @classmethod
    def singleton(cls):
        """ Access singleton """
        if not cls._singleton:
            cls._singleton = Backend()
        return cls._singleton

    def __init__(self):
        self.datadir = None
        self.passwd = None

    def setup(self, uname, datadir):
        """ Initialize backend """

        self.passwd = utils_posix.getpwnam(uname)
        logging.debug("backend: uid: %d", self.passwd.pw_uid)
        logging.debug("backend: gid: %d", self.passwd.pw_gid)

        self.datadir = datadir
        logging.debug("backend: datadir: %s", self.datadir)

        #
        # Here we are assuming that the /var/lib (or /var) dir
        # exists and has the correct permissions.
        #
        # We are also assuming that we are running with enough privs
        # to be able to create a directory there on behalf of the
        # specified uid and gid.
        #
        logging.debug("backend: datadir init: %s", self.datadir)
        utils_posix.mkdir_idempotent(self.datadir, self.passwd.pw_uid,
                                     self.passwd.pw_gid)

    def _visit(self, curpath, leaf):
        """ Callback for utils_path.depth_visit() """
        if not leaf:
            logging.debug("backend: mkdir_idempotent: %s", curpath)
            utils_posix.mkdir_idempotent(curpath, self.passwd.pw_uid,
                                         self.passwd.pw_gid)
        else:
            logging.debug("backend: touch_idempotent: %s", curpath)
            utils_posix.touch_idempotent(curpath, self.passwd.pw_uid,
                                         self.passwd.pw_gid)

    def _datadir_touch(self, components):
        """ Touch a file below datadir """
        return utils_path.depth_visit(self.datadir, components, self._visit)

    def store(self, test, message):
        """ Follows closely M-Lab specification regarding how
            to save results on the disk for scalable collection. """

        # Get time information
        thetime = time.time()
        gmt = time.gmtime(thetime)
        nanosec = int((thetime % 1.0) * 1000000000)

        #
        # Build path components.
        #
        # The time format is ISO8601, except that we use nanosecond
        # and not microsecond precision.
        #
        components = [
            time.strftime('%Y', gmt),
            time.strftime('%m', gmt),
            time.strftime('%d', gmt),
            '%s.%09dZ_%s.gz' % (
                time.strftime('%Y%m%dT%H:%M:%S', gmt),
                nanosec, test)]

        #
        # Make sure that the path exists and that ownership
        # and permissions are OK.
        #
        fullpath = self._datadir_touch(components)

        #
        # Open the output file for appending, write into
        # it the message and close.
        #
        # We open for appending just in case two tests
        # terminates at the same time (unlikely!).
        #
        filep = gzip.open(fullpath, 'ab')
        json.dump(message, filep)
        filep.close()

def setup(uname, datadir):
    """ Initialize backend """
    Backend.singleton().setup(uname, datadir)

def store(test, message):
    """ Follows closely M-Lab specification regarding how
        to save results on the disk for scalable collection. """
    Backend.singleton().store(test, message)
