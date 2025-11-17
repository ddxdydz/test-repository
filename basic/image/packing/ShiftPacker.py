from typing import TypeAlias

import numpy as np

from basic.image.packing.ABC_Packer import Packer


class ShiftPacker(Packer):
    def __init__(self, bits_per_value: int = 8):
        super().__init__(bits_per_value)

    def get_padded(self, array_flat: np.ndarray, dtype: TypeAlias, bytes_count: int) -> np.ndarray:
        try:
            array_size = array_flat.size
            values_per_byte = bytes_count // self.bits_per_value
            padded_length = ((array_size + (values_per_byte - 1)) // values_per_byte) * values_per_byte
            padded = np.zeros(padded_length, dtype=dtype)
            padded[:array_size] = array_flat
            return padded
        except Exception as ex:
            print(f"Error in ShiftPacker.get_padded {dtype} {bytes_count}")
            raise Exception

    def pack_array(self, array: np.ndarray) -> bytes:
        """Упаковка через сдвиги с сохранением формы массива"""
        self._validate_array(array)

        array_flat = array.flatten()

        if self.bits_per_value == 1:
            packed_array = np.packbits(array_flat).tobytes()
        elif self.bits_per_value == 2:  # 4 values for 1 np.uint8
            padded = self.get_padded(array_flat, np.uint8, 8)
            packed = (padded[0::4] << 6) | (padded[1::4] << 4) | (padded[2::4] << 2) | padded[3::4]
            packed_array = packed.tobytes()
        elif self.bits_per_value == 3:  # 5 values for 1 np.uint16
            padded = self.get_padded(array_flat, np.uint16, 16)
            packed = (padded[0::5] << 13) | (padded[1::5] << 10) | (padded[2::5] << 7) | (padded[3::5] << 4) | (padded[4::5] << 1)
            packed_array = packed.tobytes()
        elif self.bits_per_value == 4:  # 2 values for 1 np.uint8
            padded = self.get_padded(array_flat, np.uint8, 8)
            packed = (padded[0::2] << 4) | padded[1::2]
            packed_array = packed.tobytes()
        elif self.bits_per_value == 5:  # 3 values for 1 np.uint16
            padded = self.get_padded(array_flat, np.uint16, 16)
            packed = (padded[0::3] << 11) | (padded[1::3] << 6) | (padded[2::3] << 1)
            packed_array = packed.tobytes()
        elif self.bits_per_value == 6:  # 5 values for 1 np.uint32
            padded = self.get_padded(array_flat, np.uint32, 32)
            packed = (padded[0::5] << 26) | (padded[1::5] << 20) | (padded[2::5] << 14) | (padded[3::5] << 8) | (padded[4::5] << 2)
            packed_array = packed.tobytes()
        elif self.bits_per_value == 7:
            packed_array = array_flat.tobytes()
        elif self.bits_per_value == 8:
            packed_array = array_flat.tobytes()
        else:
            raise ValueError("ShiftPacker.pack: self.bits_per_value not in 1-8")

        # Добавляем заголовок с формой
        header = self._pack_shape(array.shape)

        return header + packed_array

    def unpack_array(self, data: bytes) -> np.ndarray:
        """Распаковка через сдвиги с восстановлением формы из заголовка"""
        # Распаковываем заголовок
        shape, packed_array = self._unpack_shape_header(data)
        expected_size = int(np.prod(shape))

        if self.bits_per_value == 1:
            arr = np.frombuffer(packed_array, dtype=np.uint8)
            unpacked = np.unpackbits(arr)
            result = unpacked[:expected_size].reshape(shape)
        elif self.bits_per_value == 2:
            arr = np.frombuffer(packed_array, dtype=np.uint8)
            unpacked_size = arr.size * 4
            unpacked = np.zeros(unpacked_size, dtype=np.uint8)
            unpacked[0::4] = (arr >> 6) & 0x3
            unpacked[1::4] = (arr >> 4) & 0x3
            unpacked[2::4] = (arr >> 2) & 0x3
            unpacked[3::4] = arr & 0x3
            result = unpacked[:expected_size].reshape(shape)
        elif self.bits_per_value == 3:
            arr = np.frombuffer(packed_array, dtype=np.uint16)
            unpacked_size = arr.size * 5
            unpacked = np.zeros(unpacked_size, dtype=np.uint8)
            unpacked[0::5] = (arr >> 13) & 0x7
            unpacked[1::5] = (arr >> 10) & 0x7
            unpacked[2::5] = (arr >> 7) & 0x7
            unpacked[3::5] = (arr >> 4) & 0x7
            unpacked[4::5] = (arr >> 1) & 0x7
            result = unpacked[:expected_size].reshape(shape)
        elif self.bits_per_value == 4:
            arr = np.frombuffer(packed_array, dtype=np.uint8)
            unpacked_size = arr.size * 2
            unpacked = np.zeros(unpacked_size, dtype=np.uint8)
            unpacked[0::2] = (arr >> 4) & 0xF
            unpacked[1::2] = arr & 0xF
            result = unpacked[:expected_size].reshape(shape)
        elif self.bits_per_value == 5:
            arr = np.frombuffer(packed_array, dtype=np.uint16)
            unpacked_size = arr.size * 3
            unpacked = np.zeros(unpacked_size, dtype=np.uint8)
            unpacked[0::3] = (arr >> 11) & 0x1F
            unpacked[1::3] = (arr >> 6) & 0x1F
            unpacked[2::3] = (arr >> 1) & 0x1F
            result = unpacked[:expected_size].reshape(shape)
        elif self.bits_per_value == 6:
            arr = np.frombuffer(packed_array, dtype=np.uint32)
            unpacked_size = arr.size * 5
            unpacked = np.zeros(unpacked_size, dtype=np.uint8)
            unpacked[0::5] = (arr >> 26) & 0x3F
            unpacked[1::5] = (arr >> 20) & 0x3F
            unpacked[2::5] = (arr >> 14) & 0x3F
            unpacked[3::5] = (arr >> 8) & 0x3F
            unpacked[4::5] = (arr >> 2) & 0x3F
            result = unpacked[:expected_size].reshape(shape)
        elif self.bits_per_value == 7:
            result = np.frombuffer(packed_array, dtype=np.uint8).reshape(shape)
        elif self.bits_per_value == 8:
            result = np.frombuffer(packed_array, dtype=np.uint8).reshape(shape)
        else:
            raise ValueError("ShiftPacker.unpack: self.bits_per_value not in 1-8")

        return result
