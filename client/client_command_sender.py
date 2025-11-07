import socket
import time
from enum import Enum

import pyautogui
from pynput import mouse, keyboard
from pynput.keyboard import KeyCode, Key
from pynput.mouse import Button

from support.KEY_NAME_TO_NUM import KEY_NAME_TO_NUM


class Action(Enum):  # 16 действий максимум
    ON_MOVE = 1
    ON_CLICK_RELEASED_LEFT = 2
    ON_CLICK_RELEASED_RIGHT = 3
    ON_CLICK_PRESSED_LEFT = 4
    ON_CLICK_PRESSED_RIGHT = 5
    ON_SCROLL = 6
    ON_PRESS_REGULAR = 7
    ON_PRESS_SPECIAL = 8
    ON_RELEASE_REGULAR = 9
    ON_RELEASE_SPECIAL = 10


class CommandRecorderClient:
    SOCKET = None
    CALIBRATION_VALUES = [0, 0]
    _last_move_time: float = 0
    MOVE_COOLDOWN = 0.2  # минимальный интервал между командами движения в секундах
    SCREEN_SIZE = [0, 0]

    def __init__(self, server_host, server_port=8888):
        self.server_host = server_host
        self.server_port = server_port

        self.is_recording = False
        self.keyboard_listener = None
        self.mouse_listener = None

    def connect(self):
        CommandRecorderClient.SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        CommandRecorderClient.SOCKET.connect((self.server_host, self.server_port))
        CommandRecorderClient.SOCKET.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        CommandRecorderClient.SOCKET.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 8)
        CommandRecorderClient.SOCKET.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 8)
        print(f"CommandRecorderClient - Connected to server {self.server_host}:{self.server_port}")

    @staticmethod
    def close():
        CommandRecorderClient.SOCKET.close()

    @staticmethod
    def process_command(action: Enum, val1: int, val2: int):
        if CommandRecorderClient.SOCKET is None:
            print(f"CommandRecorderClient - socket not connected: {action.name} {val1} {val2}")
            return False

        # Для команд движения проверяем cooldown
        if action == Action.ON_MOVE:
            current_time = time.time()
            if current_time - CommandRecorderClient._last_move_time < CommandRecorderClient.MOVE_COOLDOWN:
                return True
            CommandRecorderClient._last_move_time = current_time

        # Для команд с x y проверяем диапазон
        if CommandRecorderClient.SCREEN_SIZE[0] and CommandRecorderClient.SCREEN_SIZE[1]:
            if 0 < action.value < 6:
                if val1 < 0 or val1 > CommandRecorderClient.SCREEN_SIZE[0]:
                    return True
                if val2 < 0 or val2 > CommandRecorderClient.SCREEN_SIZE[1]:
                    return True

        try:
            action = action.value

            # Проверяем диапазоны
            if not (0 <= action <= 15):
                raise ValueError("action must be 0-15 (4 bits)")
            if not (0 <= val1 <= 16383):  # 2^14 - 1
                raise ValueError("val1 must be 0-16383 (14 bits)")
            if not (0 <= val2 <= 16383):  # 2^14 - 1
                raise ValueError("val2 must be 0-16383 (14 bits)")

            # Собираем команду
            command_int = (action << 28) | (val1 << 14) | val2
            data = command_int.to_bytes(4, byteorder='big', signed=False)
            CommandRecorderClient.SOCKET.sendall(data)

            return True
        except Exception as e:
            print(f"Error sending command: {e}")
            return False

    @staticmethod
    def calibrate(x, y):
        return ((x + CommandRecorderClient.CALIBRATION_VALUES[0],
                y + CommandRecorderClient.CALIBRATION_VALUES[1]))

    @staticmethod
    def reset_calibration(pg_x, pg_y):
        gl_x, gl_y = pyautogui.position()
        CommandRecorderClient.CALIBRATION_VALUES[0] = pg_x - gl_x
        CommandRecorderClient.CALIBRATION_VALUES[1] = pg_y - gl_y
        print(f"CALIBRATION_VALUES is {CommandRecorderClient.CALIBRATION_VALUES} now")

    @staticmethod
    def on_move(x: int, y: int) -> bool:
        CommandRecorderClient.process_command(Action.ON_MOVE, *CommandRecorderClient.calibrate(x, y))
        return True

    @staticmethod
    def on_click(x: int, y: int, button: Button, pressed: bool) -> bool:
        if button == Button.left:
            cx, cy = CommandRecorderClient.calibrate(x, y)
            if pressed:
                CommandRecorderClient.process_command(Action.ON_CLICK_PRESSED_LEFT, cx, cy)
            else:
                CommandRecorderClient.process_command(Action.ON_CLICK_RELEASED_LEFT, cx, cy)
        elif button == Button.right:
            cx, cy = CommandRecorderClient.calibrate(x, y)
            if pressed:
                CommandRecorderClient.process_command(Action.ON_CLICK_PRESSED_RIGHT, cx, cy)
            else:
                CommandRecorderClient.process_command(Action.ON_CLICK_RELEASED_RIGHT, cx, cy)
        return True

    @staticmethod
    def on_scroll(x: int, y: int, dx: int, dy: int) -> bool:
        # dx + 1, dy + 1 (отрицательные значения не передаются)
        CommandRecorderClient.process_command(Action.ON_SCROLL, dx + 1, dy + 1)
        return True

    @staticmethod
    def on_press(key: (Key | KeyCode | None)) -> None:
        try:
            if hasattr(key, 'char') and key.char is not None:
                CommandRecorderClient.process_command(Action.ON_PRESS_REGULAR, ord(key.char), 0)
            elif key == Key.space:
                CommandRecorderClient.process_command(Action.ON_PRESS_REGULAR, ord(' '), 0)
            elif isinstance(key, Key):
                CommandRecorderClient.process_command(Action.ON_PRESS_SPECIAL, KEY_NAME_TO_NUM[key.name], 2)
        except Exception as e:
            print(f"Error in on_press: {e}")

    @staticmethod
    def on_release(key: (Key | KeyCode | None)) -> None:
        try:
            if hasattr(key, 'char') and key.char is not None:
                CommandRecorderClient.process_command(Action.ON_RELEASE_REGULAR, ord(key.char), 0)
            elif key == Key.space:
                CommandRecorderClient.process_command(Action.ON_RELEASE_REGULAR, ord(' '), 0)
            elif isinstance(key, Key):
                CommandRecorderClient.process_command(Action.ON_RELEASE_SPECIAL, KEY_NAME_TO_NUM[key.name], 2)
        except Exception as e:
            print(f"Error in on_release: {e}")

    def start(self):
        self.keyboard_listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release,
            suppress=False
        )
        self.mouse_listener = mouse.Listener(
            on_move=self.on_move,
            on_click=self.on_click,
            on_scroll=self.on_scroll,
            suppress=False
        )
        self.keyboard_listener.start()
        self.mouse_listener.start()
        self.is_recording = True
        print("CommandRecorderClient - Recording started.")

    def stop(self):
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        if self.mouse_listener:
            self.mouse_listener.stop()
        self.is_recording = False
        print("CommandRecorderClient - Recording stopped.")


if __name__ == "__main__":
    recorder = CommandRecorderClient('localhost', 3215)
    # recorder.SCREEN_SIZE[0], recorder.SCREEN_SIZE[1] = 640, 480
    # recorder.connect()
    recorder.start()
    help(Key)
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        recorder.stop()
        if recorder.SOCKET:
            recorder.SOCKET.close()
