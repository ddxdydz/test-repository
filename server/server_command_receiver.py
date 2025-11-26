import socket
from typing import List

import pyautogui

from basic.network.ABC_Server import Server
from basic.network.SocketTransceiver import SocketTransceiver, SocketTransceiverError
from basic.network.actions_transfer.Action import Action
from basic.network.actions_transfer.key_maps import KEY_MAP_NUM_TO_NAME


class CommandReceiverServer(Server):
    def __init__(self, host='0.0.0.0', port=0, enable_executing: bool = True):
        super().__init__(host, port)
        self.name = self.__class__.__name__
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 8)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 8)

        pyautogui.FAILSAFE = False

        self._current_modifiers = {
            'ctrl_l': False, 'ctrl_r': False, 'alt_l': False, 'alt_r': False, 'shift': False, 'cmd': False
        }

        self.enable_executing = enable_executing
        self.command_comment = "executed: " if enable_executing else "passed: "

    @staticmethod
    def _check_xy_range(x: int, y: int):
        width, height = pyautogui.size()
        return 0 <= x <= width and 0 <= y <= height

    def get_current_modifiers(self) -> List[str]:
        result = []
        if self._current_modifiers['ctrl_l'] or self._current_modifiers['ctrl_r']:
            result.append('ctrl')
        if self._current_modifiers['alt_l'] or self._current_modifiers['alt_r']:
            result.append('alt')
        return result

    def process(self, action: Action, val1: int, val2: int):
        try:
            if action == Action.ON_MOVE and self._check_xy_range(val1, val2):
                if self.enable_executing:
                    pyautogui.moveTo(val1, val2)
                print(self.command_comment, action, (val1, val2), pyautogui.position())
            elif action == Action.ON_CLICK_RELEASED_LEFT and self._check_xy_range(val1, val2):
                if self.enable_executing:
                    pyautogui.mouseUp(val1, val2, button='left')
                print(self.command_comment, action, (val1, val2), pyautogui.position())
            elif action == Action.ON_CLICK_RELEASED_RIGHT and self._check_xy_range(val1, val2):
                if self.enable_executing:
                    pyautogui.mouseUp(val1, val2, button='right')
                print(self.command_comment, action, (val1, val2), pyautogui.position())
            elif action == Action.ON_CLICK_PRESSED_LEFT and self._check_xy_range(val1, val2):
                if self.enable_executing:
                    pyautogui.mouseDown(val1, val2, button='left')
                print(self.command_comment, action, (val1, val2), pyautogui.position())
            elif action == Action.ON_CLICK_PRESSED_RIGHT and self._check_xy_range(val1, val2):
                if self.enable_executing:
                    pyautogui.mouseDown(val1, val2, button='right')
                print(self.command_comment, action, (val1, val2), pyautogui.position())
            elif action == Action.ON_SCROLL:
                if self.enable_executing:
                    pyautogui.hscroll(val1 - 1)
                    pyautogui.vscroll(val2 - 1)
                print(self.command_comment, action, (val1 - 1, val2 - 1), pyautogui.position())
            elif action == Action.ON_PRESS_REGULAR:
                key_name = chr(val1)
                if self.enable_executing:
                    pyautogui.keyDown(key_name)
                print(self.command_comment, action, (val1, val2), key_name)
            elif action == Action.ON_RELEASE_REGULAR:
                key_name = str(chr(val1))
                if self.enable_executing:
                    modifiers = self.get_current_modifiers()
                    pyautogui.keyUp(key_name)
                    if modifiers:
                        modifiers.append(key_name)
                        pyautogui.hotkey(*modifiers)
                        print(self.command_comment, f"+{key_name}", modifiers)
                print(self.command_comment, action, (val1, val2), key_name)
            elif action == Action.ON_PRESS_SPECIAL:
                key_name = KEY_MAP_NUM_TO_NAME[val1]
                if key_name in self._current_modifiers.keys():
                    self._current_modifiers[key_name] = True
                if self.enable_executing:
                    pyautogui.keyDown(key_name)
                print(self.command_comment, action, (val1, val2), key_name, self._current_modifiers)
            elif action == Action.ON_RELEASE_SPECIAL:
                key_name = KEY_MAP_NUM_TO_NAME[val1]
                if key_name in self._current_modifiers.keys():
                    self._current_modifiers[key_name] = False
                if self.enable_executing:
                    pyautogui.keyUp(key_name)
                print(self.command_comment, action, (val1, val2), key_name, self._current_modifiers)
            else:
                print(f"Unknown action: {action}")
        except Exception as e:
            print(f"Process command error: {str(e)}")
            raise e

    def client_loop(self, client_socket, address):
        socket_transceiver = SocketTransceiver(client_socket)
        socket_transceiver.set_timeout(None)
        print(f"{self.name}: start client_loop.")
        try:
            while True:
                command_data = socket_transceiver.recv_raw(4)
                command_int = int.from_bytes(command_data[:4], byteorder='big', signed=False)
                action = Action((command_int >> 28) & 0b1111)  # первые 4 бита - action, биты 28-31 (4 бита)
                val1 = (command_int >> 14) & 0b11111111111111  # следующие 14 битов - val1, биты 14-27 (14 бит)
                val2 = command_int & 0b11111111111111  # оставшиеся 14 битов - val2, биты 0-13 (14 бит)
                self.process(action, val1, val2)
        except (SocketTransceiverError, ConnectionResetError, ConnectionAbortedError) as e:
            print(f"{self.name}: {e}")
            print(f"{self.name}: end client_loop.")
        except Exception as e:
            print(f"{self.name}: {e}")
            raise e


if __name__ == "__main__":
    server = CommandReceiverServer(port=8000, enable_executing=True)
    server.start()
