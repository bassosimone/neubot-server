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

""" Configurable variables """

CONFIG = {
    "bittorrent.address": "",
    "bittorrent.bytes.down": 0,
    "bittorrent.bytes.up": 0,
    "bittorrent.infohash": "",
    "bittorrent.listen": False,
    "bittorrent.negotiate": True,
    "bittorrent.negotiate.port": 8080,
    "bittorrent.my_id": "",
    "bittorrent.numpieces": 1 << 20,
    "bittorrent.piece_len": 1 << 17,
    "bittorrent.port": 6881,
    "bittorrent.watchdog": 300,
    "negotiate.parallelism": 7,
    "negotiate.min_thresh": 32,
    "negotiate.max_thresh": 64,
    "prefer_ipv6": 0,
}
