from abc import ABC, abstractmethod
from typing import List

import numpy as np


class Packer(ABC):
    """Абстрактный базовый класс для упаковщиков"""

    def __init__(self, bits_per_value: int, array_shape: List[int]):
        if not (0 < bits_per_value <= 8):
            raise ValueError(f"Number of bits_per_value must be between 1 and 8, got {bits_per_value}")

        if not array_shape:
            raise ValueError("Array shape cannot be empty")

        for i, dim_size in enumerate(array_shape):
            if dim_size < 1:
                raise ValueError(f"All array dimensions must be positive, got {dim_size} at dimension {i}")

        self.bits_per_value = bits_per_value
        self.array_shape = array_shape
        self.total_elements = np.prod(array_shape)

        self.max_value = 2 ** bits_per_value

        # Вычисляем размер упакованных данных в байтах
        total_bits = self.total_elements * bits_per_value
        self.packed_size = (total_bits + 7) // 8  # Округление вверх

    def validate_array(self, array: np.ndarray) -> None:
        """Проверяет соответствие массива параметрам упаковщика.

        Args:
            array: Проверяемый массив

        Raises:
            ValueError: Если массив не соответствует ожидаемой форме или типу
            TypeError: Если массив не является numpy.ndarray
        """
        if not isinstance(array, np.ndarray):
            raise TypeError(f"Expected numpy.ndarray, got {type(array)}")

        if array.shape != tuple(self.array_shape):
            raise ValueError(f"Array shape {array.shape} doesn't match expected shape {tuple(self.array_shape)}")

        # Проверяем, что массив имеет тип uint8
        if array.dtype != np.uint8:
            raise ValueError(f"Array must have dtype uint8, got {array.dtype}")

        # Проверяем, что значения помещаются в заданное количество бит
        if array.min() < 0:
            raise ValueError(
                f"Array contains negative values {array.min()}, but packer doesn't support signed values")

        if array.max() > self.max_value:
            raise ValueError(
                f"Array values up to {array.max()} exceed maximum packable " +
                f"value {self.max_value} for {self.bits_per_value} bits")

    @abstractmethod
    def pack_array(self, array: np.ndarray) -> bytes:
        pass

    @abstractmethod
    def unpack_array(self, data: bytes) -> np.ndarray:
        pass

    def __str__(self) -> str:
        return (f"{self.__class__.__name__}(bits={self.bits_per_value}, "
                f"shape={self.array_shape}, elements={self.total_elements})")

    def __repr__(self) -> str:
        return (f"{self.__class__.__name__}(bits_per_value={self.bits_per_value}, "
                f"array_shape={self.array_shape})")
