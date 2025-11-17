import numpy as np
from numba import njit, prange

from basic.image.packing.ABC_Packer import Packer


class NumbaPacker(Packer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def calculate_packed_size(self, array: np.ndarray) -> Tuple[int, int]:
        total_bits = array.size * self.bits_per_value
        data_size = (total_bits + 7) // 8  # Округление вверх
        # Размер заголовка: 2 байт для количества измерений + 2 байта на каждое измерение
        header_size = 2 + len(array.shape) * 2
        return header_size, data_size

    @njit(parallel=True)
    def pack_array(self, array: np.ndarray) -> bytes:
        result = np.zeros(self.calculate_packed_size(array), dtype=np.uint8)
        for i in prange(array.size):
            value = array[i]
            start_bit = i * self.bits_per_value
            for bit in range(self.bits_per_value):
                if value & (1 << bit):
                    byte_pos = (start_bit + bit) // 8
                    bit_pos = 7 - ((start_bit + bit) % 8)  # big-endian порядок
                    result[byte_pos] |= (1 << bit_pos)
        return result.tobytes()

    @njit(parallel=True)
    def unpack_array(self, data: bytes) -> np.ndarray:
        result = np.zeros(self.calculate_packed_size(array), dtype=np.uint32)
        total_bits = len(data) * 8

        for i in prange(output_size):
            start_bit = i * self.bits_per_value
            value = 0
            for bit in range(self.bits_per_value):
                current_bit = start_bit + bit
                if current_bit < total_bits:
                    byte_pos = current_bit // 8
                    bit_pos = 7 - (current_bit % 8)  # согласованность с pack_image
                    if data[byte_pos] & (1 << bit_pos):
                        value |= (1 << bit)
            result[i] = value
        return result
