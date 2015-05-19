# neubot/log.py

#
# Copyright (c) 2010-2011 Simone Basso <bassosimone@gmail.com>,
#  NEXA Center for Internet & Society at Politecnico di Torino
# Copyright (c) 2012 Marco Scopesi <marco.scopesi@gmail.com>
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

import sys
import logging
import traceback

from neubot.config import CONFIG

from neubot import system

def stderr_logger(severity, message):
    if severity not in ('INFO', 'ACCESS'):
        sys.stderr.write('%s: %s\n' % (severity, message))
    else:
        sys.stderr.write('%s\n' % message)

class Logger(object):

    """Logging object.  Usually there should be just one instance
       of this class, accessible with the default logging object LOG."""

    def __init__(self):
        self.logger = stderr_logger

    def redirect(self):
        self.logger = system.get_background_logger()

    def log(self, severity, message, args, exc_info):
        ''' Really log a message '''
        try:
            self._log(severity, message, args, exc_info)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            pass

    def _log(self, severity, message, args, exc_info):
        ''' Really log a message '''

        # No point in logging empty lines
        if not message:
            return

        #
        # Honor verbose.  We cannot leave this choice to the
        # "root" logger because all messages must be passed
        # to the streaming feature.  Hence the "root" logger
        # must always be configured to be vebose.
        #
        if not CONFIG['verbose'] and severity == 'DEBUG':
            return

        # Lazy processing
        if args:
            message = message % args
        if exc_info:
            exc_list = traceback.format_exception(exc_info[0],
                                                  exc_info[1],
                                                  exc_info[2])
            message = "%s\n%s\n" % (message, ''.join(exc_list))
            for line in message.split('\n'):
                self._log(severity, line, None, None)
            return

        message = message.rstrip()

        # Write to the current logger object
        self.logger(severity, message)

def oops(message="", func=None):
    if not func:
        func = logging.error
    if message:
        func("OOPS: " + message + " (traceback follows)")
    for line in traceback.format_stack()[:-1]:
        func(line)

LOG = Logger()

class LogWrapper(logging.Handler):

    """Wrapper for stdlib logging."""

    def emit(self, record):
        msg = record.msg
        args = record.args
        level = record.levelname
        exc_info = record.exc_info
        LOG.log(level, msg, args, exc_info)

ROOT_LOGGER = logging.getLogger()
# Make sure all previously registered handlers go away
ROOT_LOGGER.handlers = []
ROOT_LOGGER.addHandler(LogWrapper())
ROOT_LOGGER.setLevel(logging.DEBUG)

def set_verbose():
    ''' Make logger verbose '''
    CONFIG['verbose'] = 1
