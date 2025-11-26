import socket
from time import sleep
from typing import Tuple, Dict

import numpy as np

from basic.image.ToolsManager import ToolsManager
from basic.network.SocketTransceiver import SocketTransceiver, SocketTransceiverError
from basic.network.size_constants import *
from basic.network.tools.time_ms import time_ms


class ScreenReceiverClient:
    SOCKET_TIMEOUT = 10

    def __init__(self, server_host, server_port=8888, colors: int = 3, scale_percent: int = 60):
        self.name = self.__class__.__name__
        self._server_host = server_host
        self._server_port = server_port

        _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        _socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        _socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
        _socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)
        self._socket_transceiver = SocketTransceiver(_socket)
        self._socket_transceiver.set_timeout(self.SOCKET_TIMEOUT)

        self.width, self.height, self.colors, self.scale_percent = 1, 1, colors, scale_percent
        self.tools_manager = ToolsManager()

    def get_screen_size(self) -> Tuple[int, int]:
        return self.width, self.height

    def connect(self) -> bool:
        self._socket_transceiver.connect((self._server_host, self._server_port))
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

    @staticmethod
    def read_data(data: bytes) -> dict:
        result_dict = dict()
        result_dict["index"] = int.from_bytes(data[:SCREEN_INDEX_SIZE], 'big')
        offset = SCREEN_INDEX_SIZE
        result_dict["screenshotted_time_ms"] = int.from_bytes(data[offset:offset + SCREEN_TIME_SIZE], 'big')
        offset += SCREEN_TIME_SIZE
        result_dict["encoded_time_ms"] = int.from_bytes(data[offset:offset + SCREEN_TIME_SIZE], 'big')
        offset += SCREEN_TIME_SIZE
        result_dict["cursor_x"] = int.from_bytes(data[offset:offset + SCREEN_CURSOR_X_SIZE], 'big')
        offset += SCREEN_CURSOR_X_SIZE
        result_dict["cursor_y"] = int.from_bytes(data[offset:offset + SCREEN_CURSOR_Y_SIZE], 'big')
        offset += SCREEN_CURSOR_Y_SIZE
        result_dict["data"] = data[offset:]
        return result_dict

    def recv_screen(self) -> Dict:
        # Sending request, Receiving
        _request_time_ms = time_ms()
        self._socket_transceiver.send_raw(b"\x01")
        received = self._socket_transceiver.recv_framed()
        sleep(0.2)  # задержка сети
        _received_time_ms = time_ms()

        # Screen decoding
        result_dict = self.read_data(received)
        stats, result_dict["data"] = self.tools_manager.decode_image(result_dict["data"])
        _decode_time = time_ms()

        # Debug
        index_str = str(result_dict["index"])
        align = "".ljust(len(index_str))
        print(f"{f"{index_str}: "}{_received_time_ms}: {len(received)} B is received for {_received_time_ms - _request_time_ms} ms!")
        print(f"{f"{align}  "}{_decode_time}: {len(received)} B is decoded for {time_ms(stats["total_time"])} ms!")

        # Stats
        result_dict["size"] = len(received)
        result_dict["request_time_ms"] = _request_time_ms
        result_dict["received_time_ms"] = _received_time_ms
        result_dict["received_time_ms"] = _received_time_ms
        result_dict["decoded_time_ms"] = _decode_time

        return result_dict

    def close(self):
        self._socket_transceiver.close()

    def show(self, image_array: np.ndarray):
        self.tools_manager.show_decoded_image(image_array)


if __name__ == "__main__":
    client = ScreenReceiverClient('192.168.56.1', 8888)
    if client.connect():
        client.recv_screen()
        # client.recv_screen()
        # client.show(client.recv_screen()["data"])
    client.close()
