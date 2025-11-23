import socket
from time import time, strftime, gmtime

from PIL import Image

from alegacy.image.ImageCompressor import ImageCompressor
from basic.network.SocketTransceiver import recv_with_header_size


class ScreenReceiverClient:
    def __init__(self, server_host, server_port=8888):
        self.server_host = server_host
        self.server_port = server_port
        self.screen_recv_count = 0

    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 524288)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 524288)

        self.socket.connect((self.server_host, self.server_port))
        print(f"ScreenReceiverClient - Connected to server {self.server_host}:{self.server_port}")

    def start(self):
        data = recv_with_header_size(self.socket)
        self.width = int.from_bytes(data[:4], byteorder='big', signed=False)
        self.height = int.from_bytes(data[4:8], byteorder='big', signed=False)
        print("ScreenReceiverClient - screen size params is configured:", self.width, self.height)
        compression = int.from_bytes(data[8:12], byteorder='big', signed=False)
        quantization = int.from_bytes(data[12:16], byteorder='big', signed=False)
        colors_count = int.from_bytes(data[16:20], byteorder='big', signed=False)
        self.compressor = ImageCompressor(compression, quantization, colors_count)
        print("ScreenReceiverClient - compression params is configured:", self.compressor.get_info())

    def get_screen_size(self):
        return self.width, self.height

    def close(self):
        self.socket.close()

    def recv_screen_bytes(self) -> (int, bytes):
        self.screen_recv_count += 1
        print(f"CLIENT screen#{self.screen_recv_count}: start receiving ({strftime('%H:%M:%S', gmtime())})...")

        start_time = time()
        screenshot_bytes = recv_with_header_size(self.socket)
        if not screenshot_bytes:
            print(f"CLIENT screen#{self.screen_recv_count}: Received Error!")
        time_to_recv_screen = time() - start_time

        start_time = time()
        weight = len(screenshot_bytes)
        img_bytes = self.compressor.decompress_to_bytes(screenshot_bytes, (self.width, self.height))
        time_to_decompress = time() - start_time

        total_time = time_to_recv_screen + time_to_decompress
        print(f"CLIENT screen#{self.screen_recv_count} is recv ({strftime('%H:%M:%S', gmtime())})!")
        print(f" - time_to_recv_screen:{round(time_to_recv_screen, 4)}с")
        print(f" - time_to_decompress:{round(time_to_decompress, 4)}с",
              f"({len(img_bytes) // 1024}KB -> {weight // 1024}KB)")
        print(f" - total_time:{round(total_time, 4)}с")

        self.socket.sendall(b'\x01')  # Подтверждение успешного получения
        return weight, img_bytes

    def recv_screen_image(self) -> Image:
        img_weight, image_bytes = self.recv_screen_bytes()
        print("Получен скриншот:", f"{img_weight // 1024}KB", "->", f"{len(image_bytes) // 1024}KB")
        return Image.frombytes('RGB', (self.width, self.height), image_bytes)


if __name__ == "__main__":
    # client = ScreenReceiverClient('51.250.45.221', 39865)
    client = ScreenReceiverClient('158.160.205.94', 33293)
    client.connect()
    client.start()
    # from time import time
    # while True:
    #     start = time()
    screen = client.recv_screen_image()
    #     print(time() - start)
    screen = client.recv_screen_image()
    screen = client.recv_screen_image()
    screen = client.recv_screen_image()
    screen.show()
    client.close()
