from typing import TypeAlias

import numpy as np

from basic.image.packing.ABC_Packer import Packer


class ShiftPacker(Packer):
    _TYPES_MAP = {
        # bits_per_value: (dtype, dtype_bits_count, values_per_dtype)
        1: (np.uint8, 8, 8),
        2: (np.uint8, 8, 4),
        3: (np.uint16, 16, 5),
        4: (np.uint8, 8, 2),
        5: (np.uint16, 16, 3),
        6: (np.uint32, 32, 5),
        7: (np.uint64, 64, 9),
        8: (np.uint8, 8, 1),
    }
    _MASK_MAP = {1: 0b00000001, 2: 0b00000011, 3: 0b00000111, 4: 0b00001111,
                 5: 0b00011111, 6: 0b00111111, 7: 0b01111111, 8: 0b11111111}
    _SHIFTS_MAP = dict()
    for bits_per_value in range(1, 9):
        dtype, dtype_bits_count, values_per_dtype = _TYPES_MAP[bits_per_value]
        _SHIFTS_MAP[bits_per_value] = bits_per_value * np.arange(values_per_dtype, dtype=dtype)[::-1]
    # print(*list(_SHIFTS_MAP.items()), sep="\n")

    def __init__(self, bits_per_value: int = 8):
        super().__init__(bits_per_value)

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

            tamped = np.zeros(aligned_length // values_per_dtype, dtype=target_dtype)
            for value_pos_in_dtype, shift in enumerate(shifts):
                tamped |= (aligned_array[value_pos_in_dtype::values_per_dtype] << shift)

            return tamped
        except Exception as ex:
            print(f"ShiftPacker._tamp_array_by_shift: Tamping failed for {bits_per_value} bits: ")
            raise ex

    @staticmethod
    def _untamp_array_by_shift(tamped_array: np.ndarray, bits_per_value: int,
                               expected_size: int, values_per_dtype: int) -> np.ndarray:
        try:
            bit_mask = ShiftPacker._MASK_MAP[bits_per_value]
            shifts = ShiftPacker._SHIFTS_MAP[bits_per_value]

            untamped = np.zeros(tamped_array.size * values_per_dtype, dtype=np.uint8)
            for value_pos_in_dtype, shift in enumerate(shifts):
                untamped[value_pos_in_dtype::values_per_dtype] = (tamped_array >> shift) & bit_mask

            return untamped[:expected_size]
        except Exception as ex:
            print(f"ShiftPacker._untamp_array_by_shift: Untamping failed for {bits_per_value} bits: ")
            raise ex

    def pack_array(self, array: np.ndarray) -> bytes:
        """Упаковка через сдвиги с сохранением формы массива"""
        self._validate_array(array)

        flatten_array = array.flatten()

        if self.bits_per_value == 1:
            packed_array = np.packbits(flatten_array).tobytes()
        elif self.bits_per_value == 8:
            packed_array = flatten_array.tobytes()
        elif self.bits_per_value in (2, 3, 4, 5, 6, 7):
            dtype, dtype_bits_count, values_per_dtype = ShiftPacker._TYPES_MAP[self.bits_per_value]
            tamped_array = self._tamp_array_by_shift(flatten_array, self.bits_per_value, dtype, values_per_dtype)
            packed_array = tamped_array.tobytes()
        else:
            raise ValueError("ShiftPacker.pack: self.bits_per_value not in 1-8")

        header = self._pack_shape(array.shape)  # Запаковываем заголовок
        return header + packed_array

    def unpack_array(self, data: bytes) -> np.ndarray:
        """Распаковка через сдвиги с восстановлением формы из заголовка"""
        shape, packed_array = self._unpack_shape_header(data)  # Распаковываем заголовок
        expected_size = int(np.prod(shape))

        if self.bits_per_value == 1:
            arr = np.frombuffer(packed_array, dtype=np.uint8)
            unpacked = np.unpackbits(arr)
            array = unpacked[:expected_size].reshape(shape)
        elif self.bits_per_value == 8:
            array = np.frombuffer(packed_array, dtype=np.uint8).reshape(shape)
        elif self.bits_per_value in (2, 3, 4, 5, 6, 7):
            dtype, dtype_bits_count, values_per_dtype = ShiftPacker._TYPES_MAP[self.bits_per_value]
            untamped_array = np.frombuffer(packed_array, dtype=dtype)
            array = self._untamp_array_by_shift(untamped_array, self.bits_per_value,
                                                expected_size, values_per_dtype).reshape(shape)
        else:
            raise ValueError("ShiftPacker.unpack: self.bits_per_value not in 1-8")

        self._validate_array(array)

        return array
