#
# Copyright (c) 2015
#   Nexa Center for Internet & Society, Politecnico di Torino (Italy)
#   and Simone Basso <bassosimone@gmail.com>.
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

""" Neubot logging wrappers """

import logging
import sys
import syslog
import traceback

class StderrFormatter(logging.Formatter):
    """ Reproduces Neubot original formatting on stderr """

    def format(self, record):
        msg = logging.Formatter.format(self, record)
        if record.levelname in ('INFO', 'ACCESS'):
            return msg
        return record.levelname + ": " + msg

class BackgroundLogger(logging.Handler):
    """ Syslog handler """

    #
    # Implemented using syslog becuse SysLogHandler is
    # difficult to use: you need to know the path to the
    # system specific ``/dev/log``.
    #

    def __init__(self):
        logging.Handler.__init__(self)
        syslog.openlog('neubot', syslog.LOG_PID, syslog.LOG_DAEMON)

    def emit(self, record):
        try:

            #
            # Note: no format-string worries here since Python does 'the right
            # thing' in Modules/syslogmodule.c:
            #
            # >    syslog(priority, "%s", message);
            #
            msg = record.msg % record.args
            if record.levelname == 'ERORR':
                syslog.syslog(syslog.LOG_ERR, msg)
            elif record.levelname == 'WARNING':
                syslog.syslog(syslog.LOG_WARNING, msg)
            elif record.levelname == 'DEBUG':
                syslog.syslog(syslog.LOG_DEBUG, msg)
            else:
                syslog.syslog(syslog.LOG_INFO, msg)

        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            pass

class Logger(object):
    """ Neubot logger object """

    _singleton = None

    def __init__(self):
        self._root = logging.getLogger()
        self._handler = logging.StreamHandler(sys.stderr)
        self._handler.setFormatter(StderrFormatter())
        self._root.handlers = []  # Start over
        self._root.addHandler(self._handler)
        self._root.setLevel(logging.INFO)

    def redirect(self):
        """ Redirect logger to syslog """
        self._root.removeHandler(self._handler)
        self._handler = BackgroundLogger()
        self._root.addHandler(self._handler)

    def set_verbose(self):
        """ Make the logger verbose """
        self._root.setLevel(logging.DEBUG)

    @classmethod
    def singleton(cls):
        """ Initialize singleton """
        if not cls._singleton:
            cls._singleton = Logger()
        return cls._singleton

def log_access(msg, *args, **kwargs):
    """ Log access message """
    logging.info("ACCESS: " + msg, *args, **kwargs)

def oops(message=""):
    """ Write oops message """
    if message:
        logging.warning("OOPS: " + message + " (traceback follows)")
    for line in traceback.format_stack()[:-1]:
        logging.warning(line)

def redirect():
    """ Redirect logger to syslog """
    Logger.singleton().redirect()

def set_verbose():
    """ Make the logger verbose """
    Logger.singleton().set_verbose()

# Force creation of instance
Logger.singleton()
