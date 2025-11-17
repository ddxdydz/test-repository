import numpy as np

from basic.image.packing.ABC_Packer import Packer


class ShiftPacker2(Packer):
    _TYPES_MAP = {
        # bits_per_value: (dtype, dtype_bits_count, values_per_dtype)
        1: (np.uint8, 8, 8),
        2: (np.uint8, 8, 4),
        3: (np.uint16, 16, 5),
        4: (np.uint8, 8, 2),
        5: (np.uint16, 16, 3),
        6: (np.uint32, 32, 5),
        7: (np.uint8, 8, 1),
        8: (np.uint8, 8, 1),
    }
    _MASK_MAP = {1: 0b00000001, 2: 0b00000011, 3: 0b00000111, 4: 0b00001111,
                 5: 0b00011111, 6: 0b00111111, 7: 0b01111111, 8: 0b11111111}
    _SHIFTS_MAP = dict()
    for bits_per_value in range(1, 9):
        dtype, dtype_bits_count, values_per_dtype = _TYPES_MAP[bits_per_value]
        _SHIFTS_MAP[bits_per_value] = dtype_bits_count - bits_per_value * (np.arange(values_per_dtype, dtype=dtype) + 1)

    def __init__(self, bits_per_value: int = 8):
        super().__init__(bits_per_value)

    @staticmethod
    def _pack_array_shift(array_flat: np.ndarray, bits_per_value: int) -> bytes:
        try:
            dtype, dtype_bits_count, values_per_dtype = ShiftPacker2._TYPES_MAP[bits_per_value]
            shifts = ShiftPacker2._SHIFTS_MAP[bits_per_value]

            padded_length = ((array_flat.size + (values_per_dtype - 1)) // values_per_dtype) * values_per_dtype
            if padded_length > array_flat.size:
                padded = np.empty(padded_length, dtype=dtype)
                padded[:array_flat.size] = array_flat
                padded[array_flat.size:] = 0
            else:
                padded = array_flat.astype(dtype)

            packed = np.zeros(padded_length // values_per_dtype, dtype=dtype)
            for value_pos_in_dtype, shift in enumerate(shifts):
                packed |= (padded[value_pos_in_dtype::values_per_dtype] << shift)

            # reshaped = padded.reshape(-1, values_per_dtype)  # Переформатируем массив для векторной обработки
            # packed = np.sum(reshaped << shifts, axis=1, dtype=dtype)  # Векторная операция упаковки

            return packed.tobytes()
        except Exception as ex:
            print(f"ShiftPacker2._pack_array_shift: Packing failed for {bits_per_value} bits")
            raise ex

    @staticmethod
    def _unpack_array_shift(packed_array: bytes, bits_per_value: int, expected_size: int) -> np.ndarray:
        try:
            dtype, dtype_bits_count, values_per_dtype = ShiftPacker2._TYPES_MAP[bits_per_value]
            bit_mask = ShiftPacker2._MASK_MAP[bits_per_value]
            shifts = ShiftPacker2._SHIFTS_MAP[bits_per_value]

            arr = np.frombuffer(packed_array, dtype=dtype)

            unpacked = np.zeros(arr.size * values_per_dtype, dtype=np.uint8)
            for value_pos_in_dtype, shift in enumerate(shifts):
                unpacked[value_pos_in_dtype::values_per_dtype] = (arr >> shift) & bit_mask

            # arr_expanded = np.repeat(arr, values_per_dtype)  # Повторяем массив для векторной обработки
            # shifts_tiled = np.tile(shifts, arr.size)  # Создаем матрицу сдвигов
            # unpacked = (arr_expanded >> (dtype_bits_count - shifts_tiled - bits_per_value)) & bit_mask

            return unpacked[:expected_size]
        except Exception as ex:
            raise ValueError(f"ShiftPacker2._unpack_array_shift: Unpacking failed for {bits_per_value} bits. {ex}")

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
            raise ValueError("ShiftPacker2.pack: self.bits_per_value not in 1-8")

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
            raise ValueError("ShiftPacker2.unpack: self.bits_per_value not in 1-8")

        self._validate_array(array)

        return array
