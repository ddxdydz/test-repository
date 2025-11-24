import socket
from time import time, sleep
from typing import Tuple, Dict

import numpy as np

from basic.image.ToolsManager import ToolsManager
from basic.network.SocketTransceiver import SocketTransceiver, SocketTransceiverError
from basic.network.size_constants import *


class ScreenReceiverClient:
    SOCKET_TIMEOUT = 10

    def __init__(self, server_host, server_port=8888, colors: int = 3, scale_percent: int = 60):
        self.name = self.__class__.__name__
        self._server_host = server_host
        self._server_port = server_port
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        self._socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)
        self._socket_transceiver = SocketTransceiver(self._socket)
        self._socket_transceiver.set_timeout(self.SOCKET_TIMEOUT)
        self.width, self.height = 1, 1
        self.colors, self.scale_percent = colors, scale_percent
        self.tools_manager = ToolsManager()

    def get_screen_size(self) -> Tuple[int, int]:
        return self.width, self.height

    def connect(self) -> bool:
        self._socket.connect((self._server_host, self._server_port))
        print(f"{self.name}: Connected to server {self._server_host}:{self._server_port}")
        try:
            # Получение параметров экрана
            self.width = int.from_bytes(self._socket_transceiver.recv_raw(SCREEN_WIDTH_SIZE), 'big')
            self.height = int.from_bytes(self._socket_transceiver.recv_raw(SCREEN_HEIGHT_SIZE), 'big')
            # Отправка параметров выходного изображения
            self._socket_transceiver.send_raw(self.colors.to_bytes(COLORS_SIZE, 'big'))
            self._socket_transceiver.send_raw(self.scale_percent.to_bytes(SCALE_PERCENT_SIZE, 'big'))
        except SocketTransceiverError as e:
            print(f"{self.name}: {e}")
            self.close()
            return False
        self.tools_manager = ToolsManager(self.width, self.height, self.colors, self.scale_percent)
        print(f"{self.name}: {self.tools_manager} is created!")
        return True

    def close(self):
        self._socket_transceiver.close()

    def recv_screen(self) -> Dict:
        self.tools_manager.print_divided_line()

        self._socket_transceiver.send_raw(b'\x01')
        send_request_time_in_ms = int(time() * 1000)
        print(f"{send_request_time_in_ms} - {self.name}: request is sent, waiting to receive...")
        screen_index = int.from_bytes(self._socket_transceiver.recv_raw(SCREEN_INDEX_SIZE), 'big')
        screen_time_in_ms = int.from_bytes(self._socket_transceiver.recv_raw(SCREEN_TIME_SIZE), 'big')
        start_sending_time_in_ms = int.from_bytes(self._socket_transceiver.recv_raw(SCREEN_TIME_SIZE), 'big')
        cursor_x = int.from_bytes(self._socket_transceiver.recv_raw(SCREEN_CURSOR_X_SIZE), 'big')
        cursor_y = int.from_bytes(self._socket_transceiver.recv_raw(SCREEN_CURSOR_Y_SIZE), 'big')
        data = self._socket_transceiver.recv_framed()
        weight = SCREEN_INDEX_SIZE + SCREEN_TIME_SIZE + SCREEN_CURSOR_X_SIZE + SCREEN_CURSOR_Y_SIZE + len(data)
        sleep(0.4)  # задержка сети
        received_time_in_ms = int(time() * 1000)
        print(f"{received_time_in_ms} - {self.name}: ({screen_index}, {weight} B) is received!")

        print(f"{int(time() * 1000)} - {self.name}: start decoding {screen_index}...")
        stats, image_array = self.tools_manager.decode_image(data)
        print(f"{int(time() * 1000)} - {self.name}: {screen_index} is decoded...")

        result = {
            "screen_index": screen_index,
            "screen_time_in_ms": screen_time_in_ms,
            "send_request_time_in_ms": send_request_time_in_ms,
            "start_sending_time_in_ms": start_sending_time_in_ms,
            "received_time_in_ms": received_time_in_ms,
            "weight": weight,
            "cursor_x": cursor_x,
            "cursor_y": cursor_y,
            "image_array": image_array
        }
        return result

    def show(self, image_array: np.ndarray):
        self.tools_manager.show_decoded_image(image_array)


if __name__ == "__main__":
    client = ScreenReceiverClient('10.173.23.76', 6732)
    if client.connect():
        client.show(client.recv_screen()["image_array"])
    client.close()
