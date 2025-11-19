from abc import ABC, abstractmethod


class Compressor(ABC):
    """Базовый класс для компрессоров"""

    def __init__(self):
        self.name = self.__class__.__name__

    @abstractmethod
    def compress(self, data: bytes) -> bytes:
        pass

    @abstractmethod
    def decompress(self, compressed_data: bytes) -> bytes:
        pass
