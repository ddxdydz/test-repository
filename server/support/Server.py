import socket
import urllib.request
from abc import ABC, abstractmethod

import pyautogui


class Server(ABC):
    def __init__(self, host='0.0.0.0', port=0):
        self.host = host
        self.port = port
        self.clients = []
        self.allowed_hosts = ['10.140.82.76', '188.162.86.103', '127.0.0.1']

        pyautogui.FAILSAFE = False  # отключает при курсоре в углу

        self.running = False

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)

    @staticmethod
    def get_network_info() -> str:
        try:
            with urllib.request.urlopen('https://api.ipify.org', timeout=5) as response:
                external_ip = response.read().decode('utf-8')
                return external_ip
        except Exception as e:
            print(f"get_network_info(): {e}")
            return '-'

    @staticmethod
    def get_info(server_socket, name="Server"):
        return f"* {name} started: {server_socket.getsockname()}" + \
            f"\n* Local IP: {socket.gethostbyname(socket.gethostname())}" + \
            f"\n* External IP: {Server.get_network_info()}"

    def start(self):
        self.running = True
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(1)
            print(self.get_info(self.server_socket, self.__class__.__name__))
            while True:
                print(f"Server.py: Waiting for client connection ({self.server_socket.getsockname()[1]})...")
                client_socket, address = self.server_socket.accept()
                self.handle_client(client_socket, address)
        except Exception as e:
            print(f"Server.py: Ошибка сервера: {e}")
        finally:
            print("Server.py: socket closed.")
            self.server_socket.close()

    def stop(self):
        print("Server.py: stop.")
        self.running = False
        for client in self.clients:
            client.close()

    def handle_client(self, client_socket, address):
        try:
            print(f"Client connected: {address}")
            self.clients.append(client_socket)
            if address[0] not in self.allowed_hosts:
                print("Address not in allowed_hosts.")
            else:
                print("Start client loop.")
                self.client_loop(client_socket, address)
        except Exception as e:
            print(f"Client error {address}: {e}")
        finally:
            self.clients.remove(client_socket)
            print(f"Client {address} connection is terminated.")
            client_socket.close()

    @abstractmethod
    def client_loop(self, client_socket, address):
        ...


if __name__ == "__main__":
    server = Server()
    try:
        server.start()
    except KeyboardInterrupt:
        print("Stopping...")
        server.stop()
