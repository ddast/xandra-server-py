# Copyright (C) 2017 Dennis Dast
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import socket
import logging
import argparse

import server

VERSION = '0.4.0'
PORT = 64296

def run():
    parser = argparse.ArgumentParser(
            prog = 'xandra',
            description = 'Start xandra server',
            epilog = '''For more information about xandra, see
                        https://github.com/ddast/xandra-server.''')
    parser.add_argument('--port', type=int, default=64296,
                        help='use this port')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-4', action='store_true', help='use only IPv4')
    group.add_argument('-6', action='store_true', help='use only IPv6')
    parser.add_argument('-v', action='store_true', default=False,
                        help='use verbose output')
    args = parser.parse_args()

    if args.v:
        logging.basicConfig(format='%(levelname)s:%(message)s',
                level=logging.DEBUG)
    else:
        logging.basicConfig(format='%(levelname)s:%(message)s')

    srv = server.Server(PORT, socket.AF_UNSPEC)
    srv.start()

if __name__ == '__main__':
    run()
