# Part of Neubot <https://neubot.nexacenter.org/>.
# Neubot is free software. See AUTHORS and LICENSE for more
# information on the copying conditions.

"""
    Runs the botticelli subprocess.

    Botticelli is a Neubot and NDT server written in Go meant to
    possibly replace this implementation and available at

        <https://github.com/neubot/botticelli>
"""

import logging
import os
import stat
import subprocess

BOTTICELLI = os.sep.join([
    os.path.dirname(os.path.dirname(os.path.dirname(
                    os.path.abspath(__file__)))),
    "bin",
    "linux_386",
    "botticelli"
])

def coroutine(poller):
    """ Coroutine that checks whether botticelli is available, runs it and
        monitors the running process, possibly restarting it """

    logging.debug("botticelli-path: %s", BOTTICELLI)

    res = None
    try:
        res = os.lstat(BOTTICELLI)
    except OSError:
        logging.warning("fatal: '%s' is missing", BOTTICELLI)
        logging.warning("You should run `./scripts/get-botticelli'")
        return

    if not stat.S_ISREG(res.st_mode):
        logging.warning("fatal: './bin/botticelli': not a regular file")
        return

    # TODO: do we need to check for more strict permissions?
    if (res.st_mode & stat.S_IXUSR) != stat.S_IXUSR:
        logging.warning("fatal: './bin/botticelli': not executable")
        return

    process = subprocess.Popen([BOTTICELLI])

    def check_botticelli():
        """ Periodically check whether botticelli is running """

        ret = process.poll()
        if ret is None:
            poller.sched(5.0, check_botticelli)
            return
        logging.warning("fatal: '%s' terminated: %s", BOTTICELLI, ret)

        def call_again():
            """ Start again the botticelli server """
            coroutine(poller)

        poller.sched(0.0, call_again)

    def cleanup():
        """ Function called when the poller exits """
        process.terminate()
        process.wait()

    poller.atexit(cleanup)
    poller.sched(5.0, check_botticelli)

def coroutine_lazy(poller):
    """ Schedule coroutine to run in five seconds """

    def call_coroutine():
        """ Really call the corutine """
        coroutine(poller)

    poller.sched(5.0, call_coroutine)

def mod_load(context, message):
    """ Invoked when the botticelli loads """
    logging.debug("botticelli: init for context '%s'... in progress", context)

    if context == "server":
        coroutine_lazy(message["poller"])

    else:
        logging.warning("botticelli: unknown context: %s", context)

    logging.debug("botticelli: init for context '%s'... complete", context)
