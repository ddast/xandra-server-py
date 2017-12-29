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

import protocol

class Server:
    def __init__(self, port, ipversion):
        self._port = port
        self._ipversion = ipversion
        self._s = None
        self._conn = None

    def start(self):
        self._print_welcome()
        self._init_socket()
        while True:
            self._accept_and_receive()

    def _print_welcome(self):
        print('Starting server on ' + socket.gethostname() + ' (' +
              socket.gethostbyname(socket.gethostname()) + ')')

    def _init_socket(self):
        for res in socket.getaddrinfo(None, self._port, self._ipversion,
                                      socket.SOCK_STREAM, 0,
                                      socket.AI_PASSIVE):
            af, socktype, proto, canonname, sa = res
            try:
                self._s = socket.socket(af, socktype, proto)
                self._s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                # TODO: set SO_RCVTIMEO to 3s
            except OSError as err:
                logging.debug('OSError: {}'.format(err))
                self._s = None
                continue
            try:
                self._s.bind(sa)
                self._s.listen(1)
            except OSError as err:
                logging.debug('OSError: {}'.format(err))
                self.stop()
                continue
            break
        if self._s is None:
            raise RunTimeError('Failed to open socket')

    def _accept_and_receive(self):
        self._conn, addr = self._s.accept()
        proto = protocol.Protocol()
        with self._conn:
            print('Connected to {}'.format(addr))
            borrow = None
            while True:
                data = self._conn.recv(128)
                if not data: break
                if borrow is not None:
                    data = borrow + data
                #print(data)
                processed = proto.process_data(data)
                if processed < len(data):
                    borrow = data[processed:]
                else:
                    borrow = None

    def stop(self):
        try:
            self._s.close()
        except OSError as err:
            logging.debug('OSError: {}'.format(err))
        self._s = None
