# neubot/system.py

#
# Copyright (c) 2011 Simone Basso <bassosimone@gmail.com>,
#  NEXA Center for Internet & Society at Politecnico di Torino
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

''' System dependent routines '''

# NB: This code is currently being refactored.

import os

if os.name == "posix":
    from .system_posix import go_background
    from .system_posix import drop_privileges
    from .system_posix import _get_profile_dir
    from .system_posix import _want_rwx_dir
    from .system_posix import _want_rw_file
    from .system_posix import get_background_logger
    from .system_posix import has_enough_privs

else:
    raise RuntimeError("Your system is not supported")

def get_default_database_path():
    ''' Get default database path '''
    return os.sep.join([ _get_profile_dir(), "database.sqlite3" ])

def check_database_path(pathname):
    ''' Make sure database path is OK '''

    pathname = os.path.abspath(pathname)

    if not has_enough_privs():
        return pathname

    _want_rwx_dir(os.path.dirname(pathname))
    _want_rw_file(pathname)
    return pathname
