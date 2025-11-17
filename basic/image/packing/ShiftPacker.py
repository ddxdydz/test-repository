from typing import Dict, Tuple, Type

import numpy as np

from basic.image.packing.ABC_Packer import Packer


class ShiftPacker(Packer):
    _TYPES_MAP: Dict[int, Tuple[Type[np.generic], int, int, int]] = {
        # bits_per_value: (dtype, dtype_bits_count, values_per_dtype, bit_mask)
        1: (np.uint8, 8, 8, 0b00000001),
        2: (np.uint8, 8, 4, 0b00000011),
        3: (np.uint16, 16, 5, 0b00000111),
        4: (np.uint8, 8, 2, 0b00001111),
        5: (np.uint16, 16, 3, 0b00011111),
        6: (np.uint32, 32, 5, 0b00111111),
        7: (np.uint8, 8, 1, 0b01111111),
        8: (np.uint8, 8, 1, 0b11111111),
    }

    def __init__(self, bits_per_value: int = 8):
        super().__init__(bits_per_value)

    @staticmethod
    def _pack_array_shift(array_flat: np.ndarray, bits_per_value: int) -> bytes:
        try:
            dtype, dtype_bits_count, values_per_dtype, _ = ShiftPacker._TYPES_MAP[bits_per_value]

            padded_length = ((array_flat.size + (values_per_dtype - 1)) // values_per_dtype) * values_per_dtype
            padded = np.zeros(padded_length, dtype=dtype)
            padded[:array_flat.size] = array_flat

            packed = np.zeros(padded_length // values_per_dtype, dtype=dtype)

            for value_pos_in_dtype in range(values_per_dtype):
                shift = dtype_bits_count - bits_per_value * (value_pos_in_dtype + 1)
                packed |= (padded[value_pos_in_dtype::values_per_dtype] << shift)

            return packed.tobytes()
        except Exception as ex:
            raise ValueError(f"ShiftPacker._pack_array_shift: Packing failed for {bits_per_value} bits") from ex

    @staticmethod
    def _unpack_array_shift(packed_array: bytes, bits_per_value: int, expected_size: int) -> np.ndarray:
        try:
            dtype, dtype_bits_count, values_per_dtype, bit_mask = ShiftPacker._TYPES_MAP[bits_per_value]

            arr = np.frombuffer(packed_array, dtype=dtype)

            unpacked_size = arr.size * values_per_dtype
            unpacked = np.zeros(unpacked_size, dtype=np.uint8)

            for value_pos_in_dtype in range(values_per_dtype):
                shift = dtype_bits_count - bits_per_value * (value_pos_in_dtype + 1)
                unpacked[value_pos_in_dtype::values_per_dtype] = (arr >> shift) & bit_mask

            return unpacked[:expected_size]
        except Exception as ex:
            raise ValueError(f"ShiftPacker._unpack_array_shift: Unpacking failed for {bits_per_value} bits. {ex}")

    def pack_array(self, array: np.ndarray) -> bytes:
        """Упаковка через сдвиги с сохранением формы массива"""
        self._validate_array(array)

        array_flat = array.flatten()

        if self.bits_per_value == 1:
            packed_array = np.packbits(array_flat).tobytes()
        elif self.bits_per_value == 7:
            packed_array = array_flat.tobytes()
        elif self.bits_per_value == 8:
            packed_array = array_flat.tobytes()
        elif self.bits_per_value in (2, 3, 4, 5, 6):
            packed_array = self._pack_array_shift(array_flat, self.bits_per_value)
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
        elif self.bits_per_value == 7:
            array = np.frombuffer(packed_array, dtype=np.uint8).reshape(shape)
        elif self.bits_per_value == 8:
            array = np.frombuffer(packed_array, dtype=np.uint8).reshape(shape)
        elif self.bits_per_value in (2, 3, 4, 5, 6):
            array = self._unpack_array_shift(packed_array, self.bits_per_value, expected_size).reshape(shape)
        else:
            raise ValueError("ShiftPacker.unpack: self.bits_per_value not in 1-8")

        self._validate_array(array)

        return array
