import socket
from abc import ABC


class Client(ABC):
    def __init__(self, server_host, server_port=8888):
        self.server_host = server_host
        self.server_port = server_port

    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.server_host, self.server_port))
        print(f"Connected to server {self.server_host}:{self.server_port}")

    def send_message(self, message=None):
        if message is None:
            message = input("Введите сообщение: ")
            self.socket.send(message.encode('utf-8'))

    def start(self):
        ...

    def close(self):
        self.socket.close()


if __name__ == "__main__":
    client = Client('localhost', 12276)
    client.connect()
    client.start()
    client.close()
