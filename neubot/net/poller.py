#
# Copyright (c) 2010, 2012, 2015
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

''' Dispatch read, write, periodic and other events '''

import logging
import errno
import select
import sched
import sys

from ..utils import ticks
from ..utils import timestamp

#
# Number of seconds between each check for timed-out
# I/O operations.
#
CHECK_TIMEOUT = 10

class Poller(sched.scheduler):

    ''' Dispatch read, write, periodic and other events '''

    #
    # We always keep the _check_timeout() event registered
    # so the scheduler is alive forever.
    #
    # We register self._poll() as the delay function and
    # in that function we either invoke select() or we
    # sleep for the requested amount of time.
    #

    def __init__(self):
        ''' Initialize '''
        sched.scheduler.__init__(self, ticks, self._poll)
        self._again = True
        self._readset = {}
        self._writeset = {}
        self._check_timeout()

    def sched(self, delta, func, *args):
        ''' Schedule task '''
        #logging.debug('poller: sched: %s, %s, %s', delta, func, args)
        self.enter(delta, 0, self._run_task, (func, args))
        return timestamp() + delta

    @staticmethod
    def _run_task(func, args):
        ''' Safely run task '''
        #logging.debug('poller: run_task: %s, %s', func, args)
        try:
            if args:
                func(args)
            else:
                func()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            logging.error('poller: run_task() failed', exc_info=1)

    def set_readable(self, stream):
        ''' Monitor for readability '''
        self._readset[stream.fileno()] = stream

    def set_writable(self, stream):
        ''' Monitor for writability '''
        self._writeset[stream.fileno()] = stream

    def unset_readable(self, stream):
        ''' Stop monitoring for readability '''
        fileno = stream.fileno()
        if fileno in self._readset:
            del self._readset[fileno]

    def unset_writable(self, stream):
        ''' Stop monitoring for writability '''
        fileno = stream.fileno()
        if fileno in self._writeset:
            del self._writeset[fileno]

    def close(self, stream):
        ''' Safely close a stream '''
        self.unset_readable(stream)
        self.unset_writable(stream)
        try:
            stream.handle_close()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            logging.error('poller: handle_close() failed', exc_info=1)

    #
    # We are very careful when accessing readset and writeset because
    # it's possible that the fileno makes reference to a stream that
    # does not exist anymore.  Consider the following example: There is
    # a stream that is both readable and writable, and so its fileno
    # is both in res[0] and res[1].  But, when we invoke the stream's
    # readable() callback there is a protocol violation and so the
    # high-level code invokes close(), and the stream is closed, and
    # hence removed from readset and writeset.  And then the stream
    # does not exist anymore, but its fileno still is in res[1].
    #

    def _call_handle_read(self, fileno):
        ''' Safely dispatch read event '''
        if fileno in self._readset:
            stream = self._readset[fileno]
            try:
                stream.handle_read()
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                logging.error('poller: handle_read() failed', exc_info=1)
                self.close(stream)

    def _call_handle_write(self, fileno):
        ''' Safely dispatch write event '''
        if fileno in self._writeset:
            stream = self._writeset[fileno]
            try:
                stream.handle_write()
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                logging.error('poller: handle_write() failed', exc_info=1)
                self.close(stream)

    def break_loop(self):
        ''' Break out of poller loop '''
        self._again = False

    def loop(self):
        ''' Poller loop '''
        while True:
            try:
                self.run()
            except (SystemExit, select.error):
                raise
            except KeyboardInterrupt:
                break  # overriden semantic: break out of poller loop NOW
            except:
                logging.error('poller: unhandled exception', exc_info=1)

    def _poll(self, timeout):
        ''' Poll for readability and writability '''

        # Immediately break out of the loop if requested to do so
        if not self._again:
            raise KeyboardInterrupt('poller: self._again is false')

        # Monitor streams readability/writability
        elif self._readset or self._writeset:

            # Get list of readable/writable streams
            try:
                res = select.select(list(self._readset.keys()),
                                    list(self._writeset.keys()),
                                    [], timeout)
            except select.error:
                code = sys.exc_info()[1][0]
                if code != errno.EINTR:
                    logging.error('poller: select() failed', exc_info=1)
                    raise

                else:
                    # Take care of EINTR
                    return

            # No error?  Fire readable and writable events
            for fileno in res[0]:
                self._call_handle_read(fileno)
            for fileno in res[1]:
                self._call_handle_write(fileno)

        # No I/O pending?  Break out of the loop.
        else:
            raise KeyboardInterrupt('poller: no I/O pending')

    def _check_timeout(self):
        ''' Dispatch the periodic event '''

        self.sched(CHECK_TIMEOUT, self._check_timeout)
        if self._readset or self._writeset:

            streams = set()
            streams.update(list(self._readset.values()))
            streams.update(list(self._writeset.values()))

            timenow = ticks()
            for stream in streams:
                if stream.handle_periodic(timenow):
                    logging.debug('poller: watchdog timeout: %s', str(stream))
                    self.close(stream)

POLLER = Poller()
