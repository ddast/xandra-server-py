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

import sys

def _supports_dual_stack():
    try:
        testsock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        testsock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, False)
        return True
    except AttributeError:
        return False
    except OSError:
        return False
    finally:
        try:
            testsock.close()
        except OSError:
            pass

class Server:
    def __init__(self, port, af):
        self._port = port
        if af == socket.AF_UNSPEC and _supports_dual_stack():
            self._use_dual_stack = True
            self._af = socket.AF_INET6
        else:
            self._use_dual_stack = False
            self._af = af

    def start(self):
        self._print_welcome()
        while True:
            with self._init_socket() as sock:
                self._accept_and_receive(sock)

    def _print_welcome(self):
        print('Starting server on "' + socket.gethostname() + '"')

    def _init_socket(self):
        for res in socket.getaddrinfo(None, self._port, self._af,
                                      socket.SOCK_STREAM, 0,
                                      socket.AI_PASSIVE):
            logging.debug("Using socket {}".format(res))
            af, socktype, proto, canonname, sa = res
            try:
                sock = socket.socket(af, socktype, proto)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                if self._use_dual_stack:
                    sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY,
                                    False)
            except OSError as err:
                logging.debug('OSError (create socket): {}'.format(err))
                sock = None
                continue
            try:
                sock.bind(sa)
                sock.listen(0)
            except OSError as err:
                logging.debug('OSError (bind, listen): {}'.format(err))
                try:
                    sock.close()
                except OSError as err2:
                    logging.debug('OSError (closing): {}'.format(err2))
                sock = None
                continue
            break
        if sock is None:
            raise RunTimeError('Failed to open socket')
        else:
            return sock

    def _accept_and_receive(self, sock):
        conn, addr = sock.accept()
        sock.close()
        conn.settimeout(3.0)
        print('Connected to {}'.format(addr))
        proto = protocol.Protocol()
        borrow = None
        with conn:
            while True:
                try:
                    data = conn.recv(128)
                except socket.timeout:
                    logging.debug('Recv timed out. Closing connection.')
                    break
                if not data: break
                if borrow is not None:
                    data = borrow + data
                #print(data)
                processed = proto.process_data(data)
                if processed < len(data):
                    borrow = data[processed:]
                else:
                    borrow = None
        print('Connection closed.')
