import numpy as np
from numba import njit, prange


@njit(parallel=True)
def pack_image(data, bits_per_color, output_size):
    """
    Упаковывает массив значений в компактный битовый формат.

    Args:
        data: входной массив значений
        bits_per_color: количество бит на одно значение (1-8)
        output_size: размер выходного массива в байтах

    Returns:
        Упакованный массив байтов
    """
    size = len(data)
    result = np.zeros(output_size, dtype=np.uint8)

    for i in prange(size):
        value = data[i]
        start_bit = i * bits_per_color
        for bit in range(bits_per_color):
            if value & (1 << bit):
                byte_pos = (start_bit + bit) // 8
                bit_pos = 7 - ((start_bit + bit) % 8)  # big-endian порядок
                result[byte_pos] |= (1 << bit_pos)
    return result


@njit(parallel=True)
def unpack_image(packed_data, bits_per_color, output_size):
    """
    Распаковывает массив из компактного битового формата.

    Args:
        packed_data: упакованный массив байтов
        bits_per_color: количество бит на одно значение (1-8)
        output_size: количество элементов в выходном массиве

    Returns:
        Распакованный массив значений
    """
    result = np.zeros(output_size, dtype=np.uint32)
    total_bits = len(packed_data) * 8

    for i in prange(output_size):
        start_bit = i * bits_per_color
        value = 0
        for bit in range(bits_per_color):
            current_bit = start_bit + bit
            if current_bit < total_bits:
                byte_pos = current_bit // 8
                bit_pos = 7 - (current_bit % 8)  # согласованность с pack_image
                if packed_data[byte_pos] & (1 << bit_pos):
                    value |= (1 << bit)
        result[i] = value
    return result


@njit
def calculate_packed_size(data_size, bits_per_color):
    """
    Вычисляет необходимый размер упакованных данных в байтах.

    Args:
        data_size: количество элементов для упаковки
        bits_per_color: количество бит на элемент

    Returns:
        Размер в байтах
    """
    total_bits = data_size * bits_per_color
    return (total_bits + 7) // 8  # округление вверх


# Пример использования
def demo_pack_unpack():
    # Создаем тестовые данные
    original_data = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], dtype=np.uint32)
    bits_per_color = 4  # 4 бита на значение (диапазон 0-15)

    # Вычисляем размер упакованных данных
    packed_size = calculate_packed_size(len(original_data), bits_per_color)
    print(f"Исходный размер: {len(original_data)} элементов")
    print(f"Упакованный размер: {packed_size} байт")
    print(f"Коэффициент сжатия: {len(original_data) * 4 / packed_size:.2f}x")

    # Упаковываем данные
    packed = pack_image(original_data, bits_per_color, packed_size)
    print(f"Упакованные данные: {packed}")

    # Распаковываем данные
    unpacked = unpack_image(packed, bits_per_color, len(original_data))
    print(f"Распакованные данные: {unpacked}")

    # Проверяем корректность
    print(f"Данные совпадают: {np.array_equal(original_data, unpacked)}")


if __name__ == "__main__":
    demo_pack_unpack()
