import socket
from typing import Tuple, Dict

import numpy as np

from basic.image.ToolsManager import ToolsManager
from basic.network.core.SocketTransceiver import SocketTransceiver, SocketTransceiverError
from basic.network.core.time_ms import time_ms
from basic.network.screen_transfer.size_constants import *


class ScreenReceiverClient:
    SOCKET_TIMEOUT = 100

    def __init__(self, server_host, server_port=8888):
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

    def connect(self):
        self._socket_transceiver.connect((self._server_host, self._server_port))
        print(f"{self.name}: Connected to server {self._server_host}:{self._server_port}")

    @staticmethod
    def read_data(data: bytes) -> dict:
        pass

    def recv_screen(self):
        # Sending request, Receiving
        _request_time_ms = time_ms()
        self._socket_transceiver.send_raw(b"\x01")
        received = self._socket_transceiver.recv_framed()
        print(time_ms() - _request_time_ms, "ms, ", len(received), "B")

    def close(self):
        self._socket_transceiver.close()


if __name__ == "__main__":
    from settings import HOST, PORT_SCREEN_SERVER
    client = ScreenReceiverClient(HOST, PORT_SCREEN_SERVER)
    client.connect()
    print(1)
    client.recv_screen()
    print(2)
    client.recv_screen()
    print(3)
    client.close()

"""
ScreenReceiverClient: Connected to server 10.233.32.76:8888
ScreenReceiverClient: ToolsManager(1920, 1080, 2, 90) is created!
1: 1774094802412: 22406 B is received for 238 ms!
   1774094802499: 22406 B is decoded for 85 ms!
2: 1774094802616: 1327 B is received for 116 ms!
   1774094802689: 1327 B is decoded for 72 ms!
3: 1774094802798: 85 B is received for 107 ms!
   1774094802873: 85 B is decoded for 73 ms!
4: 1774094802994: 1721 B is received for 120 ms!
   1774094803071: 1721 B is decoded for 75 ms!
5: 1774094803190: 85 B is received for 118 ms!
   1774094803271: 85 B is decoded for 80 ms!
"""
