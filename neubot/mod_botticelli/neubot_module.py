# Part of Neubot <https://neubot.nexacenter.org/>.
# Neubot is free software. See AUTHORS and LICENSE for more
# information on the copying conditions.

"""
    Runs the botticelli subprocess.

    Botticelli is a Neubot and NDT server written in Go meant to
    possibly replace this implementation and available at

        <https://github.com/bassosimone/botticelli>
"""

import logging
import os
import stat
import subprocess

BOTTICELLI = os.sep.join([
    os.path.dirname(os.path.dirname(os.path.dirname(
                    os.path.abspath(__file__)))),
    "bin",
    "botticelli"
])

def coroutine(poller):
    """ Coroutine that checks whether botticelli is available, runs it and
        monitors the running process, possibly restarting it """

    logging.debug("botticell-path: %s", BOTTICELLI)

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
        if not ret:
            poller.sched(5.0, check_botticelli)
            return
        logging.warning("fatal: '%s' terminated: %s", BOTTICELLI, ret)

        def call_again():
            """ Start again the botticelli server """
            coroutine(poller)

        poller.sched(0.0, call_again)

    poller.sched(5.0, check_botticelli)

def coroutine_check(poller):
    """ Make sure we're not running as root and then call coroutine """

    uid, euid, suid = os.getresuid()
    if uid == 0 or euid == 0 or suid == 0:
        raise RuntimeError("./bin/botticelli MUST NOT run as root")

    logging.info("botticelli uid: %d / %d / %d", uid, euid, suid)

    gid, egid, sgid = os.getresgid()
    if gid == 0 or egid == 0 or sgid == 0:
        raise RuntimeError("./bin/botticelli MUST NOT run as root")

    logging.info("botticelli gid: %d / %d / %d", gid, egid, sgid)

    coroutine(poller)

def coroutine_check_lazy(poller):
    """ Schedule coroutine to run in five seconds """

    def call_coroutine():
        """ Really call the corutine """
        coroutine_check(poller)

    poller.sched(5.0, call_coroutine)

def mod_load(context, message):
    """ Invoked when the botticelli loads """
    logging.debug("botticelli: init for context '%s'... in progress", context)

    if context == "server":
        coroutine_check_lazy(message["poller"])

    else:
        logging.warning("dash: unknown context: %s", context)

    logging.debug("botticelli: init for context '%s'... complete", context)
