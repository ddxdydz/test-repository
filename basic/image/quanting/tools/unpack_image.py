import numpy as np


def unpack_image(data: bytes, bits_per_color: int, pixels_count: int) -> np.ndarray:
    # Быстрая распаковка
    if bits_per_color == 1:
        arr = np.frombuffer(data, dtype=np.uint8)
        quantized = np.unpackbits(arr)[:pixels_count]
    elif bits_per_color == 2:
        arr = np.frombuffer(data, dtype=np.uint8)
        # Создаем массив нужного размера
        unpacked_size = len(arr) * 4
        unpacked = np.zeros(unpacked_size, dtype=np.uint8)
        # Распаковываем
        unpacked[0::4] = (arr >> 6) & 0x3
        unpacked[1::4] = (arr >> 4) & 0x3
        unpacked[2::4] = (arr >> 2) & 0x3
        unpacked[3::4] = arr & 0x3
        quantized = unpacked[:pixels_count]
    elif bits_per_color == 4:
        arr = np.frombuffer(data, dtype=np.uint8)
        unpacked_size = len(arr) * 2
        unpacked = np.zeros(unpacked_size, dtype=np.uint8)
        unpacked[0::2] = (arr >> 4) & 0xF
        unpacked[1::2] = arr & 0xF
        quantized = unpacked[:pixels_count]
    else:
        """Распаковка битов для общего случая"""
        arr = np.frombuffer(data, dtype=np.uint8)
        result = np.zeros(pixels_count, dtype=np.uint8)

        # Извлекаем биты используя векторные операции
        for i in range(bits_per_color):
            bit_positions = np.arange(pixels_count) * bits_per_color + i
            byte_positions = bit_positions // 8
            # Проверяем границы
            valid_mask = byte_positions < len(arr)
            bit_offsets = 7 - (bit_positions[valid_mask] % 8)

            # Извлекаем биты из исходных данных
            bits = (arr[byte_positions[valid_mask]] >> bit_offsets) & 1
            result[valid_mask] |= bits << i
        quantized = result
    return quantized
