import numpy as np

from numba import njit, prange


@njit(parallel=True)
def pack_image_t(data, bits_per_color, output_size):
    size = len(data)
    result = np.zeros(output_size, dtype=np.uint8)

    for i in prange(size):
        value = data[i]
        start_bit = i * bits_per_color
        for bit in range(bits_per_color):
            if value & (1 << bit):
                byte_pos = (start_bit + bit) // 8
                bit_pos = 7 - ((start_bit + bit) % 8)
                result[byte_pos] |= (1 << bit_pos)
    return result


def pack_image(data: np.ndarray, bits_per_color: int, size: int) -> bytes:
    """Упаковка через сдвиги - очень быстро для малых bits_per_color"""
    if bits_per_color == 1:
        return np.packbits(data).tobytes()
    elif bits_per_color == 2:
        # Упаковка 4 значений в байт
        # Дополняем до кратного 4
        padded_length = ((size + 3) // 4) * 4
        padded = np.zeros(padded_length, dtype=np.uint8)
        padded[:size] = data
        packed = (padded[0::4] << 6) | (padded[1::4] << 4) | (padded[2::4] << 2) | padded[3::4]
        return packed.tobytes()
    elif bits_per_color == 4:
        # Упаковка 2 значений в байт
        # Дополняем до четного
        padded_length = ((size + 1) // 2) * 2
        padded = np.zeros(padded_length, dtype=np.uint8)
        padded[:size] = data
        packed = (padded[0::2] << 4) | padded[1::2]
        return packed.tobytes()
    else:
        # Общий случай
        """Упаковка битов для общего случая"""
        bits_mask = (1 << bits_per_color) - 1
        # Вычисляем необходимый размер выходного буфера
        total_bits = size * bits_per_color
        output_size = (total_bits + 7) // 8
        result = np.zeros(output_size, dtype=np.uint8)
        # Упаковываем биты используя векторные операции
        for i in range(bits_per_color):
            bit_plane = ((data >> i) & 1).astype(np.uint8)
            # Распределяем биты по выходному массиву
            bit_positions = np.arange(size) * bits_per_color + i
            byte_positions = bit_positions // 8
            bit_offsets = 7 - (bit_positions % 8)  # MSB first
            # Используем np.add.at для аккуратного обновления
            mask = byte_positions < output_size
            np.add.at(result, byte_positions[mask], (bit_plane[mask] << bit_offsets[mask]).astype(np.uint8))
        return result.tobytes()