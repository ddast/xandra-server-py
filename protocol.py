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

import logging
import pynput

class Protocol:
    _heartbeat = 0x00

    _mouse_clicks = [
            pynput.mouse.Button.left,
            pynput.mouse.Button.middle,
            pynput.mouse.Button.right
            ]

    _mouse_scrolls = [1, -1]

    _modifier_keys = [
            pynput.keyboard.Key.ctrl,
            pynput.keyboard.Key.cmd,
            pynput.keyboard.Key.alt,
            ]

    _special_keys = [
            pynput.keyboard.Key.backspace,
            pynput.keyboard.Key.esc,
            pynput.keyboard.Key.tab,
            pynput.keyboard.Key.left,
            pynput.keyboard.Key.down,
            pynput.keyboard.Key.up,
            pynput.keyboard.Key.right,
            0,
            0,
            0,
            pynput.keyboard.Key.insert,
            pynput.keyboard.Key.delete,
            pynput.keyboard.Key.home,
            pynput.keyboard.Key.end,
            pynput.keyboard.Key.page_up,
            pynput.keyboard.Key.page_down,
            pynput.keyboard.Key.f1,
            pynput.keyboard.Key.f2,
            pynput.keyboard.Key.f3,
            pynput.keyboard.Key.f4,
            pynput.keyboard.Key.f5,
            pynput.keyboard.Key.f6,
            pynput.keyboard.Key.f7,
            pynput.keyboard.Key.f8,
            pynput.keyboard.Key.f9,
            pynput.keyboard.Key.f10,
            pynput.keyboard.Key.f11,
            pynput.keyboard.Key.f12
            ]

    _mouse_press = [pynput.mouse.Button.left]

    _mouse_release = [pynput.mouse.Button.left]

    def __init__(self):
        self._modifier = None
        self._keyboard = pynput.keyboard.Controller()
        self._mouse = pynput.mouse.Controller()

    def process_data(self, data):
        processed = 0
        while (len(data) > processed):
            processed_cur = self._process_next(data[processed:])
            if processed_cur is None:
                return processed
            processed = processed + processed_cur
        return processed

    def _process_next(self, data):
        processed, current = self._utf8_to_unicode(data)
        if current is None:
            if processed == 1:
                logging.debug('Malformed input.  Buffer {}'.format(data)) 
            else:
                logging.debug('Transfering {} bytes'.format(processed))
        elif processed <= 4:
            self._process_unicode_character(current)
        elif processed == 5:
            self._process_mouse_move(current)
        elif processed == 6:
            self._process_special_key(current)
        return processed

    def _process_unicode_character(self, character):
        if character == Protocol._heartbeat:
            logging.debug('Received heartbeat')
        elif character == 0x0a:
            self._type_with_modifier(pynput.keyboard.Key.enter)
        else:
            self._type_with_modifier(chr(character))

    def _type_with_modifier(self, character):
        try:
            if self._modifier is None:
                logging.debug('Typing key: {}'.format(character))
                self._keyboard.press(character)
                self._keyboard.release(character)
            else:
                logging.debug('Typing modifier+key: {}+{}'.format(
                    self._modifier, character))
                with self._keyboard.pressed(self._modifier):
                    self._keyboard.press(character)
                    self._keyboard.release(character)
        except pynput.keyboard.Controller.InvalidKeyException as err:
            logging.warning('Cannot type key: {}'.format(err))
        self._modifier = None

    def _process_mouse_move(self, action):
        distX = action>>13
        distY = action & 0x1fff
        distX = (-1 if distX & 0x1000 else 1) * (distX & 0xfff)
        distY = (-1 if distY & 0x1000 else 1) * (distY & 0xfff)
        logging.debug('Moving mouse: x={} y={}'.format(distX, distY))
        self._mouse.move(distX, distY)

    def _process_special_key(self, key):
        fullkey = key
        if key < len(Protocol._mouse_clicks):
            logging.debug('Sending mouse click: {}'.format(
                Protocol._mouse_clicks[key]))
            self._mouse.click(Protocol._mouse_clicks[key])
            return
        key = key - len(Protocol._mouse_clicks)
        if key < len(Protocol._mouse_scrolls):
            logging.debug('Scrolling mouse: dx=0, dy={}'.format(
                Protocol._mouse_scrolls[key]))
            self._mouse.scroll(0, Protocol._mouse_scrolls[key])
            return
        key = key - len(Protocol._mouse_scrolls)
        if key < len(Protocol._modifier_keys):
            if Protocol._modifier_keys[key] != self._modifier:
                logging.debug('Setting modifier key: {}'.format(
                    Protocol._modifier_keys[key]))
                self._modifier = Protocol._modifier_keys[key]
            else:
                self._modifier = None
                self._type_with_modifier(Protocol._modifier_keys[key])
            return
        key = key - len(Protocol._modifier_keys)
        if key < len(Protocol._special_keys):
            self._type_with_modifier(Protocol._special_keys[key])
            return
        key = key - len(Protocol._special_keys)
        if key < len(Protocol._mouse_press):
            logging.debug('Sending mouse press: {}'.format(
                Protocol._mouse_press[key]))
            self._mouse.press(Protocol._mouse_press[key])
            return
        key = key - len(Protocol._mouse_press)
        if key < len(Protocol._mouse_release):
            logging.debug('Sending mouse release: {}'.format(
                Protocol._mouse_release[key]))
            self._mouse.release(Protocol._mouse_release[key])
            return
        logging.warning('Unknown special key: {}'.format(fullkey))

    def _utf8_to_unicode(self, c):
        if not (c[0] & 0x80):
            return 1, c[0]
        for i in range(2,7):
            if c[0] & ((0xff>>(i+1))^0xff) == (0xff>>i)^0xff:
                if i > len(c):
                    return i, None
                res = (c[0] & 0xff>>(i+1))<<(6*(i-1))
                for j in range(1, i):
                    if (c[j] & 0xc0) != 0x80:
                        return 1, None
                    res = res | (c[j] & 0x3f)<<(6*(i-j-1))
                return i, res
        return 1, None
