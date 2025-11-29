import threading
from typing import Optional

import pyautogui

from basic.network.SocketTransceiver import SocketTransceiver
from basic.network.actions_transfer.Action import Action
from basic.network.tools.CooldownChecker import CooldownChecker


class CommandSender:
    SOCKET_TRANSCEIVER: Optional[SocketTransceiver] = None
    SOCKET_TRANSCEIVER_LOCK = threading.Lock()

    STOP_EVENT = threading.Event()

    COOLDOWN_MOUSE_MOVEMENT_CHECKER = CooldownChecker(200)
    COOLDOWN_MOUSE_MOVEMENT_CHECKER_LOCK = threading.Lock()
    COOLDOWN_KEYBOARD_REGULAR_PRESSED_CHECKER = CooldownChecker(200)
    COOLDOWN_KEYBOARD_REGULAR_PRESSED_CHECKER_LOCK = threading.Lock()
    COOLDOWN_KEYBOARD_SPECIAL_PRESSED_CHECKER = CooldownChecker(200)
    COOLDOWN_KEYBOARD_SPECIAL_PRESSED_CHECKER_LOCK = threading.Lock()

    @staticmethod
    def _check_cooldown(action: Action) -> bool:
        if action == Action.ON_MOVE:
            with CommandSender.COOLDOWN_MOUSE_MOVEMENT_CHECKER_LOCK:
                return CommandSender.COOLDOWN_MOUSE_MOVEMENT_CHECKER.check_cooldown()
        return True

    @staticmethod
    def _process_stop_event(action: Action):
        if action == Action.ON_CLICK_PRESSED_MIDDLE:
            if CommandSender.STOP_EVENT.is_set():
                CommandSender.STOP_EVENT.clear()
                print("CommandSender: started")
            else:
                CommandSender.STOP_EVENT.set()
                print("CommandSender: stopped")

    @staticmethod
    def _pack_command(action: Action, val1: int, val2: int) -> bytes:
        if not (0 <= action.value <= 15):
            raise ValueError(f"action must be 0-15 (4 bits), got {action.value}")
        if not (0 <= val1 <= 16383):  # 2^14 - 1
            raise ValueError(f"val1 must be 0-16383 (14 bits), got {val1}")
        if not (0 <= val2 <= 16383):  # 2^14 - 1
            raise ValueError(f"val2 must be 0-16383 (14 bits), got {val2}")
        command_int = (action.value << 28) | (val1 << 14) | val2
        return command_int.to_bytes(4, byteorder='big', signed=False)

    @staticmethod
    def send_command(action: Action, val1: int, val2: int) -> None:
        CommandSender._process_stop_event(action)
        if CommandSender.STOP_EVENT.is_set():
            if action == Action.ON_CLICK_PRESSED_RIGHT:
                print(*pyautogui.position())
            return
        if not CommandSender._check_cooldown(action):
            return
        with CommandSender.SOCKET_TRANSCEIVER_LOCK:
            if CommandSender.SOCKET_TRANSCEIVER is not None:
                command_data = CommandSender._pack_command(action, val1, val2)
                CommandSender.SOCKET_TRANSCEIVER.send_raw(command_data)
            else:
                print(action, val1, val2)
