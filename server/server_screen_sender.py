import socket
from typing import Tuple, Dict

import numpy as np
import pyautogui

from basic.image.ToolsManager import ToolsManager
from basic.network.ABC_Server import Server
from basic.network.SocketTransceiver import SocketTransceiver, TimeoutSocketTransceiverError, SocketTransceiverError
from basic.network.size_constants import *
from basic.network.tools.time_ms import time_ms


class ServerScreener(Server):
    SOCKET_TIMEOUT = 10
    SOCKET_REQUEST_TIMEOUT = 0.010

    def __init__(self, host='0.0.0.0', port=8888):
        super().__init__(host, port)
        self.name = self.__class__.__name__
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)

    def init_tools_manager(self, socket_transceiver: SocketTransceiver) -> ToolsManager:
        try:
            # Отправка параметров экрана
            screen_width, screen_height = pyautogui.size()
            socket_transceiver.send_raw(screen_width.to_bytes(SCREEN_WIDTH_SIZE, 'big'))
            socket_transceiver.send_raw(screen_height.to_bytes(SCREEN_HEIGHT_SIZE, 'big'))
            # Получение параметров выходного изображения
            colors = int.from_bytes(socket_transceiver.recv_raw(COLORS_SIZE), byteorder="big")
            scale_percent = int.from_bytes(socket_transceiver.recv_raw(SCALE_PERCENT_SIZE), byteorder="big")
            return ToolsManager(screen_width, screen_height, colors, scale_percent)
        except Exception as e:
            print(f"{self.name}.init_tools_manager: {e}")
            raise e

    @staticmethod
    def prepare_data_to_send(loop_index: int, tools_manager: ToolsManager) -> Tuple[int, Dict, np.ndarray, bytes]:
        _screenshotted_time_ms = time_ms()
        stats, reference, data = tools_manager.encode_image()
        cursor_x, cursor_y = pyautogui.position()
        _encoded_time_ms = time_ms()
        data_to_send_list = [
            loop_index.to_bytes(SCREEN_INDEX_SIZE, 'big'),
            _screenshotted_time_ms.to_bytes(SCREEN_TIME_SIZE, 'big'),
            _encoded_time_ms.to_bytes(SCREEN_TIME_SIZE, 'big'),
            cursor_x.to_bytes(SCREEN_CURSOR_X_SIZE, 'big'),
            cursor_y.to_bytes(SCREEN_CURSOR_Y_SIZE, 'big'),
            data
        ]
        return _encoded_time_ms - _screenshotted_time_ms, stats, reference, b''.join(data_to_send_list)

    def client_loop(self, client_socket, address):
        socket_transceiver = SocketTransceiver(client_socket)
        socket_transceiver.set_timeout(None)
        tools_manager = self.init_tools_manager(socket_transceiver)
        print(f"{self.name}: {tools_manager} is created!")
        print(f"{self.name}: start client_loop.")
        try:
            index = 0
            while True:
                index += 1

                # Screen encoding
                _encode_delta_ms, stats, reference, data_to_send = self.prepare_data_to_send(index, tools_manager)
                _encoded_time_ms = time_ms()

                # Waiting for request
                socket_transceiver.set_timeout(self.SOCKET_REQUEST_TIMEOUT)
                try:
                    socket_transceiver.recv_raw(1)
                except TimeoutSocketTransceiverError:
                    continue
                socket_transceiver.set_timeout(self.SOCKET_TIMEOUT)
                tools_manager.update_reference(reference)

                # Sending
                socket_transceiver.send_framed(data_to_send)
                _sent_time_ms = time_ms()

                # Debug
                index_str = f"{index}: "
                align = "".ljust(len(index_str))
                print(f"{index_str}{_encoded_time_ms}: Encoded for {_encode_delta_ms} ms")
                print(f"{align}{_sent_time_ms}: {len(data_to_send)} B is sent!")

        except (SocketTransceiverError, ConnectionResetError, ConnectionAbortedError) as e:
            print(f"{self.name}: {e}")
            print(f"{self.name}: end client_loop.")
        except Exception as e:
            print(f"{self.name}: {e}")
            raise e


if __name__ == "__main__":
    server = ServerScreener()
    server.start()
