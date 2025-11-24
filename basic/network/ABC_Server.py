import socket
import urllib.request
from abc import ABC, abstractmethod


class Server(ABC):
    def __init__(self, host='0.0.0.0', port=0):
        self.name = self.__class__.__name__
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    @staticmethod
    def get_external_ip() -> str:
        try:
            with urllib.request.urlopen('https://api.ipify.org', timeout=5) as response:
                external_ip = response.read().decode('utf-8')
                return external_ip
        except Exception as e:
            print(f"get_external_ip(): {e}")
            return '-'

    @staticmethod
    def get_network_info(server_socket, name="Server"):
        return f"* {name} started: {server_socket.getsockname()}" + \
            f"\n* Local IP: {socket.gethostbyname(socket.gethostname())}" + \
            f"\n* External IP: {Server.get_external_ip()}"

    def start(self):
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(1)
            print(self.get_network_info(self.server_socket, self.name))
            while True:
                print(f"{self.name}: Waiting for client connection ({self.server_socket.getsockname()[1]})...")
                client_socket, address = self.server_socket.accept()
                self.handle_client(client_socket, address)
        except Exception as e:
            print(f"{self.name}: {e}")
        finally:
            print(f"{self.name}: socket closed.")
            self.close()

    def handle_client(self, client_socket, address):
        try:
            print(f"{self.name}: Client connected: {address}")
            print(f"{self.name}: Start client loop.")
            self.client_loop(client_socket, address)
        except Exception as e:
            print(f"{self.name}: Client error {address}: {e}")
        finally:
            print(f"{self.name}: Client {address} connection is terminated.")
            client_socket.close()

    @abstractmethod
    def client_loop(self, client_socket, address):
        ...

    def close(self):
        self.server_socket.close()
