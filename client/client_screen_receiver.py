import socket
from time import sleep
from typing import Tuple, Dict

import numpy as np

from basic.image.ToolsManager import ToolsManager
from basic.network.SocketTransceiver import SocketTransceiver, SocketTransceiverError
from basic.network.size_constants import *
from basic.network.time_ms import time_ms


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
        self.index = 0

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
        self.index = 0
        return True

    def read_data(self, data: bytes) -> dict:
        result_dict = dict()
        self.index = result_dict["index"] = int.from_bytes(data[:SCREEN_INDEX_SIZE], 'big')
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
        self.index += 1
        index_str = f"{self.index}: "
        align = "".ljust(len(index_str))

        # Sending request
        self._socket_transceiver.send_raw(b"\x01")

        # Receiving
        _start_time_ms = time_ms()
        print(f"{index_str}{time_ms()} 1: request is sent, waiting to receive...")
        received = self._socket_transceiver.recv_framed()
        result_dict = self.read_data(received)
        # sleep(0.1)  # задержка сети
        result_dict["size"] = len(received)
        result_dict["received_time_ms"] = time_ms()
        print(f"{align}{time_ms()} 1: {result_dict["size"]} B is received for {time_ms() - _start_time_ms} ms!")

        # Screen decoding
        print(f"{align}{time_ms()} 2: start decoding...")
        basic_size = len(result_dict["data"])
        stats, result_dict["data"] = self.tools_manager.decode_image(result_dict["data"])
        without_reference_size = len(self.tools_manager.compress(
            self.tools_manager.pack(self.tools_manager._difference_handler.reference_frame)[-1])[-1])
        print("!!!!", basic_size, without_reference_size)
        print(f"{align}{time_ms()} 2: screen{self.index} is decoded for {time_ms(stats["total_time"])} ms!")

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
