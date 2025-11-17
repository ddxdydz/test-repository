from abc import ABC, abstractmethod
from typing import Tuple
import numpy as np

from basic.image.packing.ABC_Packer import Packer


class ShiftPacker(Packer):
    def __init__(self, bits_per_value: int):
        super().__init__(bits_per_value)

    def _pack_shape_header(self, shape_to_pack: Tuple[int, ...]) -> bytes:
        """Упаковывает информацию о форме массива в заголовок"""
        shape_array = np.array(len(shape_to_pack), dtype=np.uint16)
        # Первый байт - количество измерений
        header = bytes([ndim])
        # Далее каждое измерение как 2-байтовое целое (big-endian)
        for dim in shape:
            if dim > 65535:  # Максимальное значение для 2 байт
                raise ValueError(f"Dimension size {dim} exceeds maximum 65535 for 2-byte encoding")
            header += bytes([(dim >> 8) & 0xFF, dim & 0xFF])  # Старший и младший байты
        return header

    def _unpack_shape_header(self, data: bytes) -> Tuple[Tuple[int, ...], int]:
        """Распаковывает форму массива из заголовка и возвращает смещение"""
        ndim = data[0]  # Первый байт - количество измерений
        header_size = 1 + ndim * 2  # 1 байт + ndim * 2 байта

        shape = []
        for i in range(ndim):
            start_idx = 1 + i * 2
            # Объединяем два байта в 16-битное число
            dim = (data[start_idx] << 8) | data[start_idx + 1]
            shape.append(dim)

        return tuple(shape), header_size

    def pack_array(self, array: np.ndarray) -> bytes:
        """Упаковка через сдвиги с сохранением формы массива"""
        if array.dtype != np.uint8:
            raise ValueError("Input array must be of type uint8")

        bits_per_color = self.bits_per_value
        size = array.size
        data_flat = array.flatten()

        # Проверка на превышение максимального значения
        if np.any(data_flat > self.max_value):
            raise ValueError(f"Input values exceed maximum value {self.max_value} for {bits_per_color} bits")

        # Упаковываем данные
        if bits_per_color == 1:
            packed_data = np.packbits(data_flat).tobytes()
        elif bits_per_color == 2:
            # Упаковка 4 значений в байт
            padded_length = ((size + 3) // 4) * 4
            padded = np.zeros(padded_length, dtype=np.uint8)
            padded[:size] = data_flat
            packed = (padded[0::4] << 6) | (padded[1::4] << 4) | (padded[2::4] << 2) | padded[3::4]
            packed_data = packed.tobytes()
        elif bits_per_color == 4:
            # Упаковка 2 значений в байт
            padded_length = ((size + 1) // 2) * 2
            padded = np.zeros(padded_length, dtype=np.uint8)
            padded[:size] = data_flat
            packed = (padded[0::2] << 4) | padded[1::2]
            packed_data = packed.tobytes()
        else:
            # Общий случай для 3, 5, 6, 7, 8 бит
            packed_data = self._pack_general_case(data_flat, bits_per_color)

        # Добавляем заголовок с формой
        header = self._pack_shape_header(array.shape)

        return header + packed_data

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
        shape, header_size = self._unpack_shape_header(data)
        expected_size = np.prod(shape)

        # Получаем только данные (без заголовка)
        data_only = data[header_size:]

        if self.bits_per_value == 1:
            arr = np.frombuffer(data_only, dtype=np.uint8)
            unpacked = np.unpackbits(arr)
            result = unpacked[:expected_size].reshape(shape)
        elif self.bits_per_value == 2:
            arr = np.frombuffer(data_only, dtype=np.uint8)
            unpacked_size = len(arr) * 4
            unpacked = np.zeros(unpacked_size, dtype=np.uint8)
            unpacked[0::4] = (arr >> 6) & 0x3
            unpacked[1::4] = (arr >> 4) & 0x3
            unpacked[2::4] = (arr >> 2) & 0x3
            unpacked[3::4] = arr & 0x3
            result = unpacked[:expected_size].reshape(shape)
        elif self.bits_per_value == 4:
            arr = np.frombuffer(data_only, dtype=np.uint8)
            unpacked_size = len(arr) * 2
            unpacked = np.zeros(unpacked_size, dtype=np.uint8)
            unpacked[0::2] = (arr >> 4) & 0xF
            unpacked[1::2] = arr & 0xF
            result = unpacked[:expected_size].reshape(shape)
        else:
            result = self._unpack_general_case(data_only, shape, expected_size)

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

    for i, original_data in enumerate(test_arrays):
        print(f"\n=== Тест {i + 1} ===")
        print(f"Исходная форма: {original_data.shape}")
        print(f"Исходные данные:\n{original_data}")

        # Тестируем упаковщик для 4 бит
        packer = ShiftPacker(bits_per_value=4)
        packed = packer.pack_array(original_data)
        print(f"Размер упакованных данных: {len(packed)} байт")

        # Распаковываем
        unpacked = packer.unpack_array(packed)
        print(f"Восстановленная форма: {unpacked.shape}")
        print(f"Восстановленные данные:\n{unpacked}")

        # Проверяем корректность
        print(f"Данные совпадают: {np.array_equal(original_data, unpacked)}")

        # Покажем структуру заголовка
        shape, header_size = packer._unpack_shape_header(packed)
        print(f"Заголовок: {header_size} байт, форма: {shape}")

        # Покажем байты заголовка
        print(f"Байты заголовка: {list(packed[:header_size])}")
