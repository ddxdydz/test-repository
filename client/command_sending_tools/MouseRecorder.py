import threading
from typing import Tuple

import pyautogui
from pynput import mouse
from pynput.mouse import Button

from basic.network.actions_transfer.Action import Action
from client.command_sending_tools.CommandSender import CommandSender


class MouseRecorder:
    SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size()
    SCREEN_SIZE_LOCK = threading.Lock()

    CALIBRATION_X, CALIBRATION_Y = 0, 0
    CALIBRATION_XY_LOCK = threading.Lock()

    @staticmethod
    def reset_calibration_xy(calibration_x: int, calibration_y: int) -> None:
        with MouseRecorder.CALIBRATION_XY_LOCK:
            MouseRecorder.CALIBRATION_X = calibration_x
            MouseRecorder.CALIBRATION_Y = calibration_y

    @staticmethod
    def _calibrate_xy(x: int, y: int) -> Tuple[int, int]:
        with MouseRecorder.CALIBRATION_XY_LOCK:
            return x + MouseRecorder.CALIBRATION_X, y + MouseRecorder.CALIBRATION_Y

    @staticmethod
    def _check_xy_range(x: int, y: int):
        return 0 <= x <= MouseRecorder.SCREEN_WIDTH and 0 <= y <= MouseRecorder.SCREEN_HEIGHT

    @staticmethod
    def on_move(x: int, y: int) -> bool:
        cx, cy = MouseRecorder._calibrate_xy(x, y)
        if not MouseRecorder._check_xy_range(cx, cy):
            return True
        CommandSender.send_command(Action.ON_MOVE, cx, cy)
        return True

    @staticmethod
    def on_click(x: int, y: int, button: Button, pressed: bool) -> bool:
        cx, cy = MouseRecorder._calibrate_xy(x, y)
        if not MouseRecorder._check_xy_range(cx, cy):
            return True
        if button == Button.left:
            action = Action.ON_CLICK_PRESSED_LEFT if pressed else Action.ON_CLICK_RELEASED_LEFT
        elif button == Button.right:
            action = Action.ON_CLICK_PRESSED_RIGHT if pressed else Action.ON_CLICK_RELEASED_RIGHT
        else:
            return True
        CommandSender.send_command(action, cx, cy)
        return True

    @staticmethod
    def on_scroll(x: int, y: int, dx: int, dy: int) -> bool:
        CommandSender.send_command(Action.ON_SCROLL, dx + 1, dy + 1)  # отрицательные значения не передаются
        return True


if __name__ == "__main__":
    mouse_listener = mouse.Listener(
        on_move=MouseRecorder.on_move,
        on_click=MouseRecorder.on_click,
        on_scroll=MouseRecorder.on_scroll,
        suppress=False
    )
    mouse_listener.start()
    while True:
        pass
