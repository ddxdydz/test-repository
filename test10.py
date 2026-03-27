import socket
import threading

import numpy as np
import pyautogui
import pygame

from basic.image.compression.base_compressors import BZ2Compressor
from basic.network.core.SocketTransceiver import SocketTransceiver
from basic.network.core.time_ms import time_ms
from settings import HOST, PORT_SCREEN_SERVER


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

    @staticmethod
    def read_data(data: bytes) -> dict:
        pass

    def recv_screen(self):
        # Sending request, Receiving
        _request_time_ms = time_ms()
        print("1")
        self._socket_transceiver.send_raw(b"\x01")
        received = self._socket_transceiver.recv_framed()
        print(time_ms() - _request_time_ms, "ms, ", len(received), "B")
        return received

    def close(self):
        self._socket_transceiver.close()


def process_screen_receiving():
    try:
        while True:
            start_receiving_event.wait()
            blit_data = [time_ms(), client.recv_screen()]
            with blit_data_queue_lock:
                blit_data_queue.clear()
                blit_data_queue.append(blit_data)
    except Exception as ex:
        print(f"Pygame process_screen_receiving Error: {ex}")
        raise ex


if __name__ == "__main__":
    SCREEN_SIZE = (1024, 768)

    bz2 = BZ2Compressor()
    reference_data = np.zeros(SCREEN_SIZE[0] * SCREEN_SIZE[1], dtype=np.uint8)

    client = ScreenReceiverClient(HOST, PORT_SCREEN_SERVER)
    print(f"Connecting to server {HOST}:{PORT_SCREEN_SERVER}...")
    client.connect()
    print(f"Connected.")

    blit_data_queue = []
    blit_data_queue_lock = threading.Lock()
    start_receiving_event = threading.Event()
    process_screen_thread = threading.Thread(target=process_screen_receiving, daemon=True)
    process_screen_thread.start()

    pygame.init()
    screen = pygame.display.set_mode(SCREEN_SIZE, pygame.RESIZABLE)
    clock = pygame.time.Clock()
    running = True
    is_inactive = True
    blit_number = 0

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and is_inactive:
                if event.key == pygame.K_ESCAPE:
                    running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and is_inactive:
                    print(*pyautogui.position(), *pygame.mouse.get_pos(), sep=", ")
                if event.button == 2:
                    is_inactive = not is_inactive
                    if is_inactive:
                        start_receiving_event.clear()
                    else:
                        start_receiving_event.set()

        data = None
        with blit_data_queue_lock:
            if blit_data_queue:
                data = blit_data_queue[-1]
                blit_data_queue.clear()
        if data is not None:
            _net_time_ms, recv_data = data
            blit_number += 1
            _dec_time_ms = time_ms()
            dec_data = bz2.decompress(recv_data)
            _conv_time_ms = time_ms()
            diff_data = np.frombuffer(dec_data, dtype=np.uint8)
            reference_data = np.bitwise_xor(reference_data, diff_data)
            gray_data = reference_data.copy() * 255
            rgb_data = np.stack([gray_data, gray_data, gray_data], axis=-1)  # shape: (height*width, 3)
            screen_to_blit = pygame.image.fromstring(rgb_data.tobytes(), SCREEN_SIZE, 'RGB')
            _blit_time_ms = time_ms()
            screen.blit(screen_to_blit, (0, 0))

            caption_info_list = [
                f"{blit_number} = {len(recv_data)} B",
                f"FPS: {int(clock.get_fps())}",
                f"net_time: {str(_dec_time_ms - _net_time_ms).rjust(4, '0')} ms",
                f"dec_time: {str(_conv_time_ms - _dec_time_ms).rjust(4, '0')} ms",
                f"conv_time: {str(_blit_time_ms - _conv_time_ms).rjust(4, '0')} ms",
                f"blit_time: {str(time_ms() - _blit_time_ms).rjust(4, '0')} ms",
            ]
            pygame.display.set_caption("   ".join(caption_info_list))
        pygame.display.flip()
        clock.tick(15)

    pygame.quit()
    client.close()
