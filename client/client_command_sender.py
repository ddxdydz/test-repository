import socket
import time

import pyautogui
from pynput import keyboard, mouse

from basic.network.SocketTransceiver import SocketTransceiver
from client.command_sending_tools.CommandSender import CommandSender
from client.command_sending_tools.KeyboardRecorder import KeyboardRecorder
from client.command_sending_tools.MouseRecorder import MouseRecorder


class CommandSenderClient:
    def __init__(self, server_host, server_port=8888):
        self.name = self.__class__.__name__
        self._server_host = server_host
        self._server_port = server_port

        _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        _socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        _socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 8)
        _socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 8)
        self._socket_transceiver = SocketTransceiver(_socket)

        self.keyboard_listener = None
        self.mouse_listener = None

    @staticmethod
    def reset_calibration_xy(global_x: int, global_y: int, window_x: int = 0, window_y: int = 0) -> None:
        MouseRecorder.reset_calibration_xy(window_x - global_x, window_y - global_y)

    def connect(self):
        self._socket_transceiver.connect((self._server_host, self._server_port))
        with CommandSender.SOCKET_TRANSCEIVER_LOCK:
            CommandSender.SOCKET_TRANSCEIVER = self._socket_transceiver
        print(f"{self.name}: Connected to server {self._server_host}:{self._server_port}")

    def close(self):
        with CommandSender.SOCKET_TRANSCEIVER_LOCK:
            CommandSender.SOCKET_TRANSCEIVER = None
        self._socket_transceiver.close()

    def start(self):
        self.keyboard_listener = keyboard.Listener(
            on_press=KeyboardRecorder.on_press, on_release=KeyboardRecorder.on_release, suppress=False
        )
        self.mouse_listener = mouse.Listener(
            on_move=MouseRecorder.on_move, on_click=MouseRecorder.on_click,
            on_scroll=MouseRecorder.on_scroll, suppress=False
        )
        self.keyboard_listener.start()
        self.mouse_listener.start()
        print(f"{self.name}: Recording started")

    def stop(self):
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        if self.mouse_listener:
            self.mouse_listener.stop()
        print(f"{self.name}: Recording stopped")

    def is_running(self) -> bool:
        return self.mouse_listener.running

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


if __name__ == "__main__":
    recorder = CommandSenderClient("158.160.202.50", 8000)
    recorder.reset_calibration_xy(753, 120, 144, 40)
    recorder.connect()
    recorder.start()
    print(pyautogui.size())
    while True:
        time.sleep(0.1)
