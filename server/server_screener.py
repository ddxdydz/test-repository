import socket
import threading
from time import time, strftime, gmtime
from typing import List, Dict

import numpy as np
import pyautogui

from basic.image.ToolsManager import ToolsManager
from basic.network.ABC_Server import Server
from basic.network.SocketTransceiver import SocketTransceiver, SocketTransceiverError
from basic.network.size_constants import *


class ServerScreener(Server):
    SOCKET_TIMEOUT = 10
    READY_TO_SEND_EVENT_TIMEOUT = 2
    LATEST_STATS_MAX_ELEMENT_COUNT = 10

    def __init__(self, host='0.0.0.0', port=0):
        super().__init__(host, port)
        self.name = self.__class__.__name__
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)

    @staticmethod
    def print_stats(stats_list: List[Dict]) -> None:
        for stats in stats_list:
            print(f"Screen №{stats["screen_index"]}",
                  f"{stats["is_terminated"]}",
                  f"{stats["screen_time_in_ms"]}",
                  f"{stats["encoded_size"]} B",
                  f"{stats["total_time"]} с", sep=" - ")

    def client_loop(self, client_socket, address):
        socket_transceiver = SocketTransceiver(client_socket)
        socket_transceiver.set_timeout(self.SOCKET_TIMEOUT)

        try:
            # Отправка параметров экрана
            screen_width, screen_height = pyautogui.size()
            socket_transceiver.send_raw(screen_width.to_bytes(SCREEN_WIDTH_SIZE, 'big'))
            socket_transceiver.send_raw(screen_height.to_bytes(SCREEN_HEIGHT_SIZE, 'big'))
            # Получение параметров выходного изображения
            colors = int.from_bytes(socket_transceiver.recv_raw(COLORS_SIZE))
            scale_percent = int.from_bytes(socket_transceiver.recv_raw(SCALE_PERCENT_SIZE))
        except SocketTransceiverError as e:
            print(f"{self.name}: {e}")
            socket_transceiver.close()
            return

        tools_manager = ToolsManager(screen_width, screen_height, colors, scale_percent)
        print(f"{self.name}: {tools_manager} is created!")

        latest_stats: List[Dict] = []
        latest_difference = np.zeros((1,))
        difference_to_apply = np.zeros((1,))
        latest_data_bytes_to_send = {"screen_index": b'', "screen_time_in_ms": b'', "cursor_x": b'',
                                     "cursor_y":  b'', "data_to_send": b''}
        lock = threading.Lock()
        reference_changed_event = threading.Event()
        stop_encoding_event = threading.Event()
        ready_to_send_event = threading.Event()

        def encode_screen():
            nonlocal latest_difference, latest_data_bytes_to_send
            screen_index = 0

            while not stop_encoding_event.is_set():
                screen_index += 1
                screen_time_in_ms = int(time() * 1000)

                # Применяем разницу если была изменена reference
                if reference_changed_event.is_set():
                    tools_manager.apply_difference(difference_to_apply)
                    reference_changed_event.clear()

                # Кодируем изображение экрана
                encode_stats, difference, data = tools_manager.encode_image()

                # Обновляем статистику
                encode_stats["screen_index"] = screen_index
                encode_stats["screen_time_in_ms"] = screen_time_in_ms
                encode_stats["is_terminated"] = 0

                # Получаем позицию курсора
                cursor_x, cursor_y = pyautogui.position()

                with lock:
                    # Чтобы избежать утечки памяти при добавлении проверяем максимальный размер
                    latest_stats.append(encode_stats)
                    if len(latest_stats) > ServerScreener.LATEST_STATS_MAX_ELEMENT_COUNT:
                        latest_stats.pop(0)

                    # Если во время обработки изменилась reference
                    if reference_changed_event.is_set():
                        tools_manager.apply_difference(difference_to_apply)
                        reference_changed_event.clear()
                        encode_stats["is_terminated"] = 1
                        continue

                    # Подготавливаем данные для отправки
                    latest_data_bytes_to_send["screen_index"] = screen_index.to_bytes(SCREEN_INDEX_SIZE, 'big')
                    latest_data_bytes_to_send["screen_time_in_ms"] = screen_time_in_ms.to_bytes(SCREEN_TIME_SIZE, 'big')
                    latest_data_bytes_to_send["cursor_x"] = cursor_x.to_bytes(SCREEN_CURSOR_X_SIZE, 'big')
                    latest_data_bytes_to_send["cursor_y"] = cursor_y.to_bytes(SCREEN_CURSOR_Y_SIZE, 'big')
                    latest_data_bytes_to_send["data_to_send"] = data

                    latest_difference = difference

                ready_to_send_event.set()

        encode_thread = threading.Thread(target=encode_screen, daemon=True)
        encode_thread.start()
        print(f"{self.name}: encode_screen_thread is activated.")
        print(f"{self.name}: start client_loop.")
        try:
            while True:
                print(f"{int(time() * 1000)} - {self.name}: waiting for sending request...")
                socket_transceiver.set_timeout(None)
                socket_transceiver.recv_raw(1)  # Ожидание запроса на отправку скриншота
                socket_transceiver.set_timeout(self.SOCKET_TIMEOUT)
                print(f"{int(time() * 1000)} - {self.name}: sending request is received!")
                print(f"{int(time() * 1000)} - {self.name}: waiting for send data to be ready...")
                ready_to_send_event.wait(self.READY_TO_SEND_EVENT_TIMEOUT)
                print(f"{int(time() * 1000)} - {self.name}: waiting for lock to be enabled...")
                with lock:
                    # Отправляем все данные
                    index = latest_stats[-1]["screen_index"]
                    additional_size = SCREEN_INDEX_SIZE + SCREEN_TIME_SIZE + SCREEN_CURSOR_X_SIZE + SCREEN_CURSOR_Y_SIZE
                    encoded_size = latest_stats[-1]["encoded_size"]
                    data_size = additional_size + encoded_size
                    start_sending_time_in_ms = int(time() * 1000)
                    print(f"{start_sending_time_in_ms} - {self.name}: start sending ({index}, {data_size} B)...")
                    socket_transceiver.send_raw(latest_data_bytes_to_send["screen_index"])
                    socket_transceiver.send_raw(latest_data_bytes_to_send["screen_time_in_ms"])
                    socket_transceiver.send_raw(start_sending_time_in_ms.to_bytes(SCREEN_TIME_SIZE, 'big'))
                    socket_transceiver.send_raw(latest_data_bytes_to_send["cursor_x"])
                    socket_transceiver.send_raw(latest_data_bytes_to_send["cursor_y"])
                    socket_transceiver.send_framed(latest_data_bytes_to_send["data_to_send"])
                    print(f"{int(time() * 1000)} - {self.name}: ({index}, {data_size} B) is sent!")
                    # Обновляем разницу для применения
                    difference_to_apply = latest_difference
                    reference_changed_event.set()
                    # Очищаем статистику
                    self.print_stats(latest_stats)
                    latest_stats.clear()
                ready_to_send_event.clear()
        except SocketTransceiverError as e:
            socket_transceiver.close()
            stop_encoding_event.set()
            print(f"{self.name}: {e}")
        finally:
            socket_transceiver.close()
            stop_encoding_event.set()
            print(f"{self.name}: end client_loop.")


if __name__ == "__main__":
    server = ServerScreener()
    try:
        server.start()
    except KeyboardInterrupt:
        print("Остановка сервера...")
        server.close()
