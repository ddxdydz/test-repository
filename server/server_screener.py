import socket
from time import time, strftime, gmtime

import pyautogui
from PIL import ImageDraw

from support.ImageCompressorLZMAGS4 import ImageCompressorLZMAGS4
from support.Server import Server
from support.tools import send_with_header_size, recv_all


class ScreenSender:
    def __init__(self, client_socket: socket.socket):
        self.compressor = ImageCompressorLZMAGS4()
        self.client_socket = client_socket
        self.screen_send_count = 0

    def send_parameters_to_receiver(self):
        width, height = pyautogui.size()
        compression, quantization, colors_count = self.compressor.get_info()
        data = (width.to_bytes(4, 'big') + height.to_bytes(4, 'big') +
                compression.to_bytes(4, 'big') +
                quantization.to_bytes(4, 'big') +
                colors_count.to_bytes(4, 'big'))
        send_with_header_size(self.client_socket, data)

    def send_screen(self):
        self.screen_send_count += 1
        print(f"SERVER screen#{self.screen_send_count}: start sending ({strftime('%H:%M:%S', gmtime())})...")

        start_time = time()
        screen = pyautogui.screenshot()
        time_to_screenshotting = time() - start_time

        start_time = time()
        draw = ImageDraw.Draw(screen)  # Drawing cursor position:
        draw.circle(pyautogui.position(), radius=6, outline='black', fill='white', width=3)
        time_to_draw_cursor_position = time() - start_time

        start_time = time()
        screenshot_bytes = self.compressor.compress(screen)[0]
        time_to_compress = time() - start_time

        start_time = time()
        send_with_header_size(self.client_socket, screenshot_bytes)
        time_to_send_screen = time() - start_time

        total_time = (time_to_screenshotting + time_to_draw_cursor_position +
                      time_to_compress + time_to_send_screen)

        weight = len(screenshot_bytes) // 1024

        print(f"SERVER screen#{self.screen_send_count}({weight}KB) is send ({strftime('%H:%M:%S', gmtime())})!")
        print(f" - time_to_screenshotting:{round(time_to_screenshotting, 4)}с")
        print(f" - time_to_draw_cursor_position:{round(time_to_draw_cursor_position, 4)}с")
        print(f" - time_to_compress:{round(time_to_compress, 4)}с")
        print(f" - time_to_send_screen:{round(time_to_send_screen, 4)}с")
        print(f" - total_time:{round(total_time, 4)}с")

        # Ждём подтверждения:
        confirmation = recv_all(self.client_socket, 1)
        if confirmation == b'\x01':
            print(f"SERVER screen#{self.screen_send_count}: confirmed by client ({strftime('%H:%M:%S', gmtime())}с)")
            return True
        print(f"SERVER screen#{self.screen_send_count}: confirmation failed")
        return False


class ScreenSenderServer(Server):
    def __init__(self, host='0.0.0.0', port=0):
        super().__init__(host, port)

    def client_loop(self, client_socket, address):
        screen_sender = ScreenSender(client_socket)
        screen_sender.send_parameters_to_receiver()
        print("ScreenSenderServer: start client_loop.")
        while self.running:
            try:
                if not screen_sender.send_screen():
                    break
            except Exception as e:
                print(f"Error (ScreenSenderServer, client_loop): {e}")
                break
        print("ScreenSenderServer: end client_loop.")


if __name__ == "__main__":
    server = ScreenSenderServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("Остановка сервера...")
        server.stop()
