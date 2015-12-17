# Neubot server

This is the server of Neubot that typically runs on M-Lab servers.

Neubot is a research project on network neutrality of the Nexa
Center for Internet & Society at Politecnico di Torino (DAUIN). The
project is based on a lightweight free software program that interested
users can download and install on their computers. The program runs in
the background and periodically performs transmission tests with
test servers, hosted by the distributed Measurement Lab platform,
and (in future) with other instances of the program itself.
Transmission tests probe the Internet using various application
level protocols and test results are saved both locally and on the
test servers. The results dataset contains samples from various
Providers and is published on the web, allowing anyone to analyze
the data for research purposes.

As a collection Neubot is Copyright (c) 2010-2015 Nexa Center for
Internet & Society, Politecnico di Torino (DAUIN) <http://nexa.polito.it/>.

Each file is copyrighted by the individual contributor.

Neubot collects your Internet address along with the results, and
that is personal data under the European law.  For more details
regarding our privacy policy, please refer to the file PRIVACY, in
this directory.

## How to start the server

In order to start the server you need root privileges.

Assuming you are in the root directory of neubot-server, you can simply start
the server running:

```BASH
$ sudo bin/neubot-server-dev
```
All the loaded modules will be printed.

### Options

```BASH
sudo bin/neubot-server-dev -[dv]
```

Accepts the following options:

* `-d ` Do not demonize neubot-server.

* `-v` Makes the command more verbose.


### Known issues

You problably do not have web100 installed. In that case this warning won't
block the execution of neubot:

```
WARNING: web100: no information available
Traceback (most recent call last):
  File "/home/davide/nexa/neubot-server/neubot/web100.py", line 134, in web100_init
```



For more info: <http://www.neubot.org/>.
