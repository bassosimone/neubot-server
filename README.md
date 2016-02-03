# Neubot server

This is the server of Neubot that typically runs on M-Lab servers.

For more info on Neubot in general, see <https://neubot.nexacenter.org/>.

## How to start neubot-server

Currently neubot-server only works on Linux systems. It should also work on
BSD systems, but this was not tested. It does not work on Windows.

In order to start neubot-server you need `root` privileges. They are needed to
bind privileged ports and to assign to user `nobody` read and write permissions
of neubot-server work directory (`/var/lib/neubot`). After ports are bound and
permissions are assigned, neubot-server drops privilegeds and runs as the non
privileged `nobody` user.

Assuming you are in the root directory of neubot-server, you can simply start
the server by running:

```BASH
$ sudo bin/neubot-server-dev
```
In its default configuration, neubot-server output is quite terse; it will only
print the loaded modules implementing one test each. Shortly afterwards, the
server will become a daemon. You can change both verbosity and daemon behavior
by specifying command line options, as follows.

### Options

```BASH
sudo bin/neubot-server-dev [-dv]
```

Accepts the following options:

* `-d ` Do not demonize neubot-server.

* `-v` Makes the command more verbose.


