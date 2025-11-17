from abc import ABC, abstractmethod
from typing import Tuple

import numpy as np


class Packer(ABC):
    """Абстрактный базовый класс для упаковщиков"""
    NDIM_DTYPE = np.uint8
    SHAPE_DTYPE = np.uint16
    BYTES_PER_NDIM = 1
    BYTES_PER_DIMENSION = 2
    MAX_DIMENSIONS = 2 ** 8 - 1
    MAX_DIMENSION_SIZE = 2 ** 16 - 1

    def __init__(self, bits_per_value: int = 8):
        self.name = self.__class__.__name__
        self.bits_per_value = None
        self.max_value = None
        self.set_bits_per_value(bits_per_value)

    def set_bits_per_value(self, bits_per_value: int):
        if not (0 < bits_per_value <= 8):
            raise ValueError(f"Number of bits_per_value must be between 1 and 8, got {bits_per_value}")
        self.bits_per_value = bits_per_value
        self.max_value = 2 ** bits_per_value - 1

    def _validate_array(self, array: np.ndarray) -> None:
        """Проверяет соответствие массива параметрам упаковщика.

        Args:
            array: Проверяемый массив

        Raises:
            ValueError: Если массив не соответствует ожидаемой форме или типу
            TypeError: Если массив не является numpy.ndarray
        """
        if not isinstance(array, np.ndarray):
            raise TypeError(f"Expected numpy.ndarray, got {type(array)}")

        if array.size == 0:
            raise ValueError("Array is empty")

        if array.dtype != np.uint8:
            raise ValueError(f"Array must have dtype uint8, got {array.dtype}")

        if array.min() < 0:
            raise ValueError(
                f"Array contains negative values {array.min()}, but packer doesn't support signed values")

        if array.max() > self.max_value:
            raise ValueError(
                f"Array values up to {array.max()} exceed maximum packable " +
                f"value {self.max_value} for {self.bits_per_value} bits")

    @staticmethod
    def _validate_shape(shape: Tuple[int, ...]) -> None:
        """Проверяет корректность формы массива"""
        if not shape:
            raise ValueError(f"Shape is empty, got {shape}")
        if len(shape) > Packer.MAX_DIMENSIONS:
            raise ValueError(f"Too many dimensions: {len(shape)}")
        if min(shape) <= 0:
            raise ValueError(f"All dimensions must be positive, got {shape}")
        if max(shape) > Packer.MAX_DIMENSION_SIZE:
            raise ValueError(f"All dimensions must be <= {Packer.MAX_DIMENSION_SIZE}, got {shape}")

    @staticmethod
    def _pack_shape(shape: Tuple[int, ...]) -> bytes:
        """Упаковывает информацию о форме массива в заголовок"""
        Packer._validate_shape(shape)
        ndim_bytes = len(shape).to_bytes(Packer.BYTES_PER_NDIM)
        shape_bytes = b''.join(
            dim.to_bytes(Packer.BYTES_PER_DIMENSION)
            for dim in shape
        )
        return ndim_bytes + shape_bytes

    @staticmethod
    def _unpack_shape_header(data: bytes) -> Tuple[Tuple[int, ...], bytes]:
        """Распаковывает форму массива и возвращает (форма, оставшиеся_данные)"""
        if len(data) < Packer.BYTES_PER_NDIM:
            raise ValueError("Not enough data to read shape header")

        ndim = int.from_bytes(data[:Packer.BYTES_PER_NDIM])

        if ndim == 0:
            raise ValueError("Number of dimensions cannot be zero")

        offset = Packer.BYTES_PER_NDIM + Packer.BYTES_PER_DIMENSION * ndim

        if len(data) < offset:
            raise ValueError(f"Data too short: need {offset} bytes, got {len(data)}")

        shape = []
        for i in range(ndim):
            start = Packer.BYTES_PER_NDIM + i * Packer.BYTES_PER_DIMENSION
            end = start + Packer.BYTES_PER_DIMENSION
            dim = int.from_bytes(data[start:end])
            shape.append(dim)
        shape_tuple = tuple(shape)

        Packer._validate_shape(shape_tuple)
        return shape_tuple, data[offset:]

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
