import numpy as np
from numba import njit, prange

from basic.image.packing.ABC_Packer import Packer


class NumbaPacker(Packer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.warm_njit()

    def warm_njit(self):
        """Прогрев для различных возможных размеров входных данных, создаёт компиляторы njit заранее"""
        test_cases = [np.ones((1, 1, 1), dtype=np.uint8), np.ones((1, 1), dtype=np.uint8),
                      np.ones((1,), dtype=np.uint8),]
        initial_bits_per_value = self.bits_per_value
        for bits_per_value in range(1, 9):
            self.set_bits_per_value(bits_per_value)
            for test_data in test_cases:
                self.unpack_array(self.pack_array(test_data))
        self.set_bits_per_value(initial_bits_per_value)

    @staticmethod
    @njit(parallel=True, cache=True)
    def _pack_array_numba(array: np.ndarray, data_size: int, bits_per_value: int) -> bytes:
        result = np.zeros(data_size, dtype=np.uint8)
        for i in prange(array.size):
            value = array[i]
            start_bit = i * bits_per_value
            for bit in range(bits_per_value):
                if value & (1 << bit):
                    byte_pos = (start_bit + bit) // 8
                    bit_pos = (start_bit + bit) % 8
                    result[byte_pos] |= (1 << bit_pos)
        return result.tobytes()

    @staticmethod
    @njit(parallel=True, cache=True)
    def _unpack_array_numba(data_array: np.ndarray, total_elements: int, bits_per_value: int) -> np.ndarray:
        result = np.zeros(total_elements, dtype=np.uint8)
        total_bits = data_array.size * 8

        for i in prange(total_elements):
            start_bit = i * bits_per_value
            value = 0
            for bit in range(bits_per_value):
                current_bit = start_bit + bit
                if current_bit < total_bits:
                    byte_pos = current_bit // 8
                    bit_pos = current_bit % 8
                    if data_array[byte_pos] & (1 << bit_pos):
                        value |= (1 << bit)
            result[i] = value

        return result

    def pack_array(self, array: np.ndarray) -> bytes:
        # Предварительные вычисления вне Numba
        total_bits = array.size * self.bits_per_value
        total_bytes = (total_bits + 7) // 8

        # Вызов Numba-функции
        packed_data = self._pack_array_numba(array.flatten(), total_bytes, self.bits_per_value)

        header = self._pack_shape(array.shape)
        return header + packed_data

    def unpack_array(self, data: bytes) -> np.ndarray:
        shape, packed_data = self._unpack_shape_header(data)
        total_elements = int(np.prod(shape))

        # Конвертируем bytes в numpy array ПЕРЕД вызовом Numba
        data_array = np.frombuffer(packed_data, dtype=np.uint8)

        # Вызов Numba-функции с numpy array вместо bytes
        flat_array = self._unpack_array_numba(data_array, total_elements, self.bits_per_value)

        return flat_array.reshape(shape)
