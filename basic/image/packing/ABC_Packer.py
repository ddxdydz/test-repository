from abc import ABC, abstractmethod
from typing import Tuple

import numpy as np


class Packer(ABC):
    """Абстрактный базовый класс для упаковщиков"""

    def __init__(self, bits_per_value: int):
        if not (0 < bits_per_value <= 8):
            raise ValueError(f"Number of bits_per_value must be between 1 and 8, got {bits_per_value}")
        self.bits_per_value = bits_per_value
        self.max_value = 2 ** bits_per_value - 1

    def validate_array(self, array: np.ndarray):
        for dim in array.shape:
            if dim > 65535:  # Максимальное значение для 2 байт
                raise ValueError(f"Dimension size {dim} exceeds maximum 65535 for 2-byte encoding")

    def calculate_packed_size(self, array: np.ndarray) -> Tuple[int, int]:
        total_bits = array.size * self.bits_per_value
        data_size = (total_bits + 7) // 8  # Округление вверх
        # Добавляем размер заголовка: 2 байт для количества измерений + 2 байта на каждое измерение
        header_size = 2 + len(array.shape) * 2
        return header_size, data_size

    @abstractmethod
    def pack_array(self, array: np.ndarray) -> bytes:
        pass

    @abstractmethod
    def unpack_array(self, data: bytes) -> np.ndarray:
        pass

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(bits={self.bits_per_value})"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(bits={self.bits_per_value})"
