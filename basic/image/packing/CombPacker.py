from typing import TypeAlias

import numpy as np
from numba import njit, prange

from basic.image.packing.ShiftPacker import ShiftPacker


class CombPacker(ShiftPacker):
    def __init__(self, bits_per_value: int = 8):
        super().__init__(bits_per_value)
        self.warm_njit()

    def warm_njit(self):
        """Прогрев для различных возможных размеров входных данных, создаёт компиляторы njit заранее"""
        test_cases = [np.ones((1, 1, 1), dtype=np.uint8), np.ones((1, 1), dtype=np.uint8),
                      np.ones((1,), dtype=np.uint8),]
        initial_bits_per_value = self.bits_per_value
        for bits_per_value in self._MASK_MAP.keys():
            self.set_bits_per_value(bits_per_value)
            for test_data in test_cases:
                self.unpack_array(self.pack_array(test_data))
        self.set_bits_per_value(initial_bits_per_value)

    @staticmethod
    @njit(parallel=True, cache=True)
    def _tamp_array_by_numba(aligned_array: np.ndarray, aligned_length: int, values_per_dtype: int,
                             target_dtype: TypeAlias, shifts: np.ndarray) -> np.ndarray:
        tamped = np.zeros(aligned_length // values_per_dtype, dtype=target_dtype)
        for i in prange(len(tamped)):
            result = 0
            for value_pos_in_dtype in range(values_per_dtype):
                shift = shifts[value_pos_in_dtype]
                idx = value_pos_in_dtype + i * values_per_dtype
                result |= (aligned_array[idx] << shift)
            tamped[i] = result
        return tamped

    @staticmethod
    @njit(parallel=True, cache=True)
    def _untamp_array_by_numba(tamped_array: np.ndarray, values_per_dtype: int, bit_mask: int, shifts: np.ndarray):
        untamped = np.zeros(tamped_array.size * values_per_dtype, dtype=np.uint8)
        for value_pos_in_dtype in prange(values_per_dtype):
            shift = shifts[value_pos_in_dtype]
            for i in range(len(tamped_array)):
                idx = value_pos_in_dtype + i * values_per_dtype
                untamped[idx] = (tamped_array[i] >> shift) & bit_mask

        return untamped

    @staticmethod
    def _tamp_array_by_shift(flatted_array: np.ndarray, bits_per_value: int,
                             target_dtype: TypeAlias, values_per_dtype: int) -> np.ndarray:
        try:
            shifts = ShiftPacker._SHIFTS_MAP[bits_per_value]

            aligned_length = ((flatted_array.size + (values_per_dtype - 1)) // values_per_dtype) * values_per_dtype
            if aligned_length > flatted_array.size:
                aligned_array = np.empty(aligned_length, dtype=target_dtype)
                aligned_array[:flatted_array.size] = flatted_array
                aligned_array[flatted_array.size:] = 0
            else:
                aligned_array = flatted_array.astype(target_dtype)

            return CombPacker._tamp_array_by_numba(
                aligned_array, aligned_length, values_per_dtype, target_dtype, shifts)
        except Exception as ex:
            print(f"CombPacker._tamp_array_by_shift: Tamping failed for {bits_per_value} bits: ")
            raise ex

    @staticmethod
    def _untamp_array_by_shift(tamped_array: np.ndarray, bits_per_value: int,
                               expected_size: int, values_per_dtype: int) -> np.ndarray:
        try:
            bit_mask = ShiftPacker._MASK_MAP[bits_per_value]
            shifts = ShiftPacker._SHIFTS_MAP[bits_per_value]

            return CombPacker._untamp_array_by_numba(tamped_array, values_per_dtype, bit_mask, shifts)[:expected_size]
        except Exception as ex:
            print(f"CombPacker._untamp_array_by_shift: Untamping failed for {bits_per_value} bits: ")
            raise ex
