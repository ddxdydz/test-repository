import socket

from pynput import keyboard, mouse

from basic.network.SocketTransceiver import SocketTransceiver
from client.command_sending_tools.CommandSender import CommandSender
from client.command_sending_tools.KeyboardRecorder import KeyboardRecorder
from client.command_sending_tools.MouseRecorder import MouseRecorder
from client.settings import *


class CommandSenderClient:
    def __init__(self, server_host="localhost", server_port=PORT_COMMAND_SERVER, enable_executing: bool = False):
        self.name = self.__class__.__name__
        self._server_host = server_host
        self._server_port = server_port

        _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        _socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        _socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 8)
        _socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 8)
        self._socket_transceiver = SocketTransceiver(_socket)

        self.enable_executing = enable_executing

        self.keyboard_listener = None
        self.mouse_listener = None

    @staticmethod
    def reset_calibration_xy(window_x: int, window_y: int, remote_x: int = 0, remote_y: int = 0) -> None:
        MouseRecorder.reset_calibration_xy(remote_x - window_x, remote_y - window_y)

    @staticmethod
    def reset_calibration_by_corners(
            window_left_upper_x: int, window_left_upper_y: int,
            window_lower_right_x: int, window_lower_right_y: int,
            remote_width: int, remote_height: int) -> None:
        if remote_width < 1:
            raise ValueError(f"CommandSenderClient: remote_width must be positive, got {remote_width}")
        if remote_height < 1:
            raise ValueError(f"CommandSenderClient: remote_height must be positive, got {remote_height}")
        window_width = window_lower_right_x - window_left_upper_x
        window_height = window_lower_right_y - window_left_upper_y
        if window_width < 1:
            raise ValueError(f"CommandSenderClient: window_width({window_lower_right_x} - {window_left_upper_x}) < 1")
        if window_height < 1:
            raise ValueError(f"CommandSenderClient: window_height({window_lower_right_y} - {window_left_upper_y}) < 1")
        MouseRecorder.reset_calibration_xy(
            calibration_x=-window_left_upper_x, calibration_y=-window_left_upper_y,
            scale_x=remote_width / window_width, scale_y=remote_height / window_height
        )

    def connect(self):
        self._socket_transceiver.connect((self._server_host, self._server_port))
        with CommandSender.SOCKET_TRANSCEIVER_LOCK:
            CommandSender.SOCKET_TRANSCEIVER = self._socket_transceiver
        CommandSender.SOCKET_TRANSCEIVER.send_raw(b"\x01" if self.enable_executing else b"\x00")
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
    # Пауза на ctrl_r
    recorder = CommandSenderClient(HOST, PORT_COMMAND_SERVER, True)
    recorder.reset_calibration_xy(
        709, 372, 389, 216
    )
    # recorder.reset_calibration_by_corners(
    #     329, 210,
    #     1590, 967,
    #     1280, 768
    # )
    recorder.reset_calibration_by_corners(
        70, 8,
        1850, 1075,
        1280, 768
    )
    recorder.connect()
    recorder.start()
    while True:
        pass
