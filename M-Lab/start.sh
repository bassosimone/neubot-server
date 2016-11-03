#!/bin/sh -e

#
# Copyright (c) 2011, 2013
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

#
# Script to start Neubot on M-Lab slivers - Invoked on the sliver
# by init/initialize.sh and by init/start.sh.
#

. /etc/mlab/slice-functions

DATADIR=/var/spool/mlab_neubot
DEBUG=

if [ `id -u` -ne 0 ]; then
    echo "$0: FATAL: need root privileges" 1>&2
    exit 1
fi

#
# When a sliver crashes and is re-created, the files and the dirs below
# $DATADIR are not owned by _neubot:_neubot, therefore neubot cannot
# save the experiments results inside $DATADIR.
#
find $DATADIR -exec chown _neubot:_neubot {} \;

ADDRESS="::"
if [ -z "`get_slice_ipv6`" ]; then
    ADDRESS="0.0.0.0"
fi

# Syslog must be running otherwise we will not have logs and most importantly
# if it is not running then botticelli will not start.
$DEBUG sudo service rsyslog start

# Make sure that the unprivileged user can access the botticelli binary
$DEBUG chmod go+rx /home/mlab_neubot

$DEBUG /home/mlab_neubot/neubot/bin/neubot-server -u _neubot \
    -A $ADDRESS -D server.datadir=$DATADIR
