import numpy as np

from basic.image.packing.ABC_Packer import Packer


class ShiftPacker(Packer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def pack_array(self, data: np.ndarray) -> bytes:
        """Упаковка через сдвиги - очень быстро для малых self.bits_per_value"""
        if self.bits_per_value == 1:
            return np.packbits(data).tobytes()
        elif self.bits_per_value == 2:
            # Упаковка 4 значений в байт
            # Дополняем до кратного 4
            padded_length = ((self.total_elements + 3) // 4) * 4
            padded = np.zeros(padded_length, dtype=np.uint8)
            padded[:self.total_elements] = data
            packed = (padded[0::4] << 6) | (padded[1::4] << 4) | (padded[2::4] << 2) | padded[3::4]
            return packed.tobytes()
        elif self.bits_per_value == 4:
            # Упаковка 2 значений в байт
            # Дополняем до четного
            padded_length = ((self.total_elements + 1) // 2) * 2
            padded = np.zeros(padded_length, dtype=np.uint8)
            padded[:self.total_elements] = data
            packed = (padded[0::2] << 4) | padded[1::2]
            return packed.tobytes()
        else:
            # Общий случай
            """Упаковка битов для общего случая"""
            bits_mask = (1 << self.bits_per_value) - 1
            # Вычисляем необходимый размер выходного буфера
            total_bits = self.total_elements * self.bits_per_value
            output_size = (total_bits + 7) // 8
            result = np.zeros(self.total_elements, dtype=np.uint8)
            # Упаковываем биты используя векторные операции
            for i in range(self.bits_per_value):
                bit_plane = ((data >> i) & 1).astype(np.uint8)
                # Распределяем биты по выходному массиву
                bit_positions = np.arange(self.total_elements) * self.bits_per_value + i
                byte_positions = bit_positions // 8
                bit_offsets = 7 - (bit_positions % 8)  # MSB first
                # Используем np.add.at для аккуратного обновления
                mask = byte_positions < output_size
                np.add.at(result, byte_positions[mask], (bit_plane[mask] << bit_offsets[mask]).astype(np.uint8))
            return result.tobytes()

    def unpack_array(self, data: bytes) -> np.ndarray:
        # Быстрая распаковка
        if self.bits_per_value == 1:
            arr = np.frombuffer(data, dtype=np.uint8)
            quantized = np.unpackbits(arr)[:self.bits_per_value]
        elif self.bits_per_value == 2:
            arr = np.frombuffer(data, dtype=np.uint8)
            # Создаем массив нужного размера
            unpacked_size = len(arr) * 4
            unpacked = np.zeros(unpacked_size, dtype=np.uint8)
            # Распаковываем
            unpacked[0::4] = (arr >> 6) & 0x3
            unpacked[1::4] = (arr >> 4) & 0x3
            unpacked[2::4] = (arr >> 2) & 0x3
            unpacked[3::4] = arr & 0x3
            quantized = unpacked[:self.bits_per_value]
        elif self.bits_per_value == 4:
            arr = np.frombuffer(data, dtype=np.uint8)
            unpacked_size = len(arr) * 2
            unpacked = np.zeros(unpacked_size, dtype=np.uint8)
            unpacked[0::2] = (arr >> 4) & 0xF
            unpacked[1::2] = arr & 0xF
            quantized = unpacked[:self.bits_per_value]
        else:
            """Распаковка битов для общего случая"""
            arr = np.frombuffer(data, dtype=np.uint8)
            result = np.zeros(self.bits_per_value, dtype=np.uint8)

            # Извлекаем биты используя векторные операции
            for i in range(self.bits_per_value):
                bit_positions = np.arange(self.bits_per_value) * self.bits_per_value + i
                byte_positions = bit_positions // 8
                # Проверяем границы
                valid_mask = byte_positions < len(arr)
                bit_offsets = 7 - (bit_positions[valid_mask] % 8)

                # Извлекаем биты из исходных данных
                bits = (arr[byte_positions[valid_mask]] >> bit_offsets) & 1
                result[valid_mask] |= bits << i
            quantized = result
        return quantized
