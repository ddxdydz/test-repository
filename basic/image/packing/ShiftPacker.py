from typing import Tuple

import numpy as np

from basic.image.packing.ABC_Packer import Packer


class ShiftPacker(Packer):
    def __init__(self, bits_per_value: int = 8):
        super().__init__(bits_per_value)

    def pack_array(self, array: np.ndarray) -> bytes:
        """Упаковка через сдвиги с сохранением формы массива"""
        self._validate_array(array)

        array_flat = array.flatten()
        array_size = array.size

        if self.bits_per_value == 1:
            packed_array = np.packbits(array_flat).tobytes()
        elif self.bits_per_value == 2:  # Упаковка 4 значений в байт
            padded_length = ((array_size + 3) // 4) * 4
            padded = np.zeros(padded_length, dtype=np.uint8)
            padded[:array_size] = array_flat
            packed = (padded[0::4] << 6) | (padded[1::4] << 4) | (padded[2::4] << 2) | padded[3::4]
            packed_array = packed.tobytes()
        elif self.bits_per_value == 4:  # Упаковка 2 значений в байт
            padded_length = ((array_size + 1) // 2) * 2
            padded = np.zeros(padded_length, dtype=np.uint8)
            padded[:array_size] = array_flat
            packed = (padded[0::2] << 4) | padded[1::2]
            packed_array = packed.tobytes()
        else:  # Общий случай для 3, 5, 6, 7, 8 бит
            packed_array = self._pack_general_case(array_flat, self.bits_per_value)

        # Добавляем заголовок с формой
        header = self._pack_shape(array.shape)

        return header + packed_array

    def _pack_general_case(self, data: np.ndarray, bits_per_color: int) -> bytes:
        """Упаковка для общего случая"""
        size = data.size
        total_bits = size * bits_per_color
        output_size = (total_bits + 7) // 8
        result = np.zeros(output_size, dtype=np.uint8)

        # Упаковываем значения побитово
        for i in range(bits_per_color):
            # Получаем i-й бит каждого значения
            bit_plane = ((data >> i) & 1).astype(np.uint8)

            # Позиции битов в выходном массиве
            bit_positions = np.arange(size) * bits_per_color + i
            byte_positions = bit_positions // 8
            bit_offsets = 7 - (bit_positions % 8)  # MSB first

            # Добавляем биты в результат
            for j in range(size):
                if byte_positions[j] < output_size:
                    result[byte_positions[j]] |= (bit_plane[j] << bit_offsets[j])

        return result.tobytes()

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
            unpacked_size = len(arr) * 4
            unpacked = np.zeros(unpacked_size, dtype=np.uint8)
            unpacked[0::4] = (arr >> 6) & 0x3
            unpacked[1::4] = (arr >> 4) & 0x3
            unpacked[2::4] = (arr >> 2) & 0x3
            unpacked[3::4] = arr & 0x3
            result = unpacked[:expected_size].reshape(shape)
        elif self.bits_per_value == 4:
            arr = np.frombuffer(packed_array, dtype=np.uint8)
            unpacked_size = len(arr) * 2
            unpacked = np.zeros(unpacked_size, dtype=np.uint8)
            unpacked[0::2] = (arr >> 4) & 0xF
            unpacked[1::2] = arr & 0xF
            result = unpacked[:expected_size].reshape(shape)
        else:
            result = self._unpack_general_case(packed_array, shape, expected_size)

        return result.astype(np.uint8)

    def _unpack_general_case(self, data: bytes, shape: Tuple[int, ...], expected_size: int) -> np.ndarray:
        """Распаковка для общего случая"""
        arr = np.frombuffer(data, dtype=np.uint8)
        bits_per_color = self.bits_per_value
        result = np.zeros(expected_size, dtype=np.uint8)

        # Распаковываем значения побитово
        for i in range(bits_per_color):
            # Позиции битов во входном массиве
            bit_positions = np.arange(expected_size) * bits_per_color + i
            byte_positions = bit_positions // 8
            bit_offsets = 7 - (bit_positions % 8)  # MSB first

            # Извлекаем биты и добавляем к результату
            for j in range(expected_size):
                if byte_positions[j] < len(arr):
                    bit_value = (arr[byte_positions[j]] >> bit_offsets[j]) & 1
                    result[j] |= (bit_value << i)

        return result.reshape(shape)


# Пример использования
if __name__ == "__main__":
    # Тестируем различные формы массивов
    test_arrays = [
        np.array([[1, 2, 3], [4, 5, 6]], dtype=np.uint8),  # 2D
        np.array([1, 2, 3, 4, 5], dtype=np.uint8),  # 1D
        np.array([[[1, 2], [3, 4]], [[5, 6], [7, 8]]], dtype=np.uint8),  # 3D
    ]
    print(test_arrays[0].shape)
    print(test_arrays[1].shape)
    print(test_arrays[2].shape)

    for i, original_data in enumerate(test_arrays):
        # print(f"\n=== Тест {i + 1} ===")
        # print(f"Исходная форма: {original_data.shape}")
        # print(f"Исходные данные:\n{original_data}")

        # Тестируем упаковщик для 4 бит
        packer = ShiftPacker(bits_per_value=4)
        packed = packer.pack_array(original_data)
        # print(f"Размер упакованных данных: {len(packed)} байт")

        # Распаковываем
        unpacked = packer.unpack_array(packed)
        # print(f"Восстановленная форма: {unpacked.shape}")
        # print(f"Восстановленные данные:\n{unpacked}")

        # Проверяем корректность
        print(f"Данные совпадают: {np.array_equal(original_data, unpacked)}")

        # Покажем структуру заголовка
        # shape, header_size = packer._unpack_shape_header(packed)
        # print(f"Заголовок: {header_size} байт, форма: {shape}")

        # Покажем байты заголовка
        # print(f"Байты заголовка: {list(packed[:header_size])}")
