import socket

import pyautogui

from basic.image.ToolsManager import ToolsManager
from basic.network.ABC_Server import Server
from basic.network.SocketTransceiver import SocketTransceiver, SocketTransceiverError
from basic.network.size_constants import *
from basic.network.time_ms import time_ms


class ServerScreener(Server):
    SOCKET_TIMEOUT = 10

    def __init__(self, host='0.0.0.0', port=0):
        super().__init__(host, port)
        self.name = self.__class__.__name__
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)

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
        print(f"{self.name}: start client_loop.")
        try:
            index = 0
            while True:
                index += 1
                index_str = f"{index}: "
                align = "".ljust(len(index_str))
                # Request waiting
                print(f"{index_str}{time_ms()} 0: waiting for sending request...")
                socket_transceiver.set_timeout(None)
                socket_transceiver.recv_raw(1)  # Ожидание запроса на отправку скриншота
                socket_transceiver.set_timeout(self.SOCKET_TIMEOUT)
                # Screen encoding
                print(f"{align}{time_ms()} 2: request is received, start encoding...")
                screen_time_in_ms = time_ms()
                stats, difference, data = tools_manager.encode_image()
                encoding_time = stats["total_time"]
                applying_time, _ = tools_manager.apply_difference(difference)
                encoding_time += applying_time
                cursor_x, cursor_y = pyautogui.position()
                print(f"{align}{time_ms()} 3: screen is encoded for {time_ms(encoding_time)} ms!")
                # Sending
                start_sending_time_in_ms = time_ms()
                print(f"{align}{start_sending_time_in_ms} 4: start sending ({index}, {len(data)} B)...")
                data_to_send_list = [
                    index.to_bytes(SCREEN_INDEX_SIZE, 'big'),
                    screen_time_in_ms.to_bytes(SCREEN_TIME_SIZE, 'big'),
                    start_sending_time_in_ms.to_bytes(SCREEN_TIME_SIZE, 'big'),
                    cursor_x.to_bytes(SCREEN_CURSOR_X_SIZE, 'big'),
                    cursor_y.to_bytes(SCREEN_CURSOR_Y_SIZE, 'big'),
                    data
                ]
                socket_transceiver.send_framed(b''.join(data_to_send_list))
                print(f"{align}{time_ms()} 5: screen {len(data)} B is sent!")
        except SocketTransceiverError as e:
            socket_transceiver.close()
            print(f"{self.name}: {e}")
        except Exception as e:
            socket_transceiver.close()
            print(f"{self.name}: {e}")
            raise e
        finally:
            socket_transceiver.close()
            print(f"{self.name}: end client_loop.")


if __name__ == "__main__":
    server = ServerScreener()
    server.start()
