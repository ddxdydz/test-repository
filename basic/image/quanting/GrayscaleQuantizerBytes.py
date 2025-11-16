from PIL import Image
import numpy as np

from basic.image.quanting.GrayscaleQuantizer import GrayscaleQuantizer


class GrayscaleQuantizerBytes(GrayscaleQuantizer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Предвычисляем LUT для максимальной скорости
        self._quant_lut = np.array([self.value_to_quant(i) for i in range(256)], dtype=np.uint8)
        self._dequant_lut = np.array([self.quant_to_value(i) for i in range(self.COLORS)], dtype=np.uint8)

    def quantize_to_bytes(self, img: Image) -> bytes:
        from time import time
        if img.mode != 'RGB':
            img = img.convert('RGB')

        start = time()
        arr = np.array(img, dtype=np.uint8)
        width, height = img.size
        pixels_count = width * height
        print("arr", time() - start)

        # Супербыстрое вычисление яркости и квантование через LUT
        start = time()
        brightness = np.dot(arr, [0.299, 0.587, 0.114]).astype(np.uint8)
        print("brightness", time() - start)
        start = time()
        quantized = self._quant_lut[brightness.flatten()]
        print("quantized", time() - start)

        bits_per_color = (self.COLORS - 1).bit_length()

        # Оптимизированная упаковка через сдвиги
        return self._pack_bits_shift(quantized, bits_per_color, pixels_count)

    def _pack_bits_shift(self, data: np.ndarray, bits_per_color: int, pixels_count: int) -> bytes:
        """Упаковка через сдвиги - очень быстро для малых bits_per_color"""
        if bits_per_color == 1:
            return np.packbits(data).tobytes()
        elif bits_per_color == 2:
            # Упаковка 4 значений в байт
            # Дополняем до кратного 4
            padded_length = ((pixels_count + 3) // 4) * 4
            padded = np.zeros(padded_length, dtype=np.uint8)
            padded[:pixels_count] = data
            packed = (padded[0::4] << 6) | (padded[1::4] << 4) | (padded[2::4] << 2) | padded[3::4]
            return packed.tobytes()
        elif bits_per_color == 4:
            # Упаковка 2 значений в байт
            # Дополняем до четного
            padded_length = ((pixels_count + 1) // 2) * 2
            padded = np.zeros(padded_length, dtype=np.uint8)
            padded[:pixels_count] = data
            packed = (padded[0::2] << 4) | padded[1::2]
            return packed.tobytes()
        else:
            # Общий случай
            return self._pack_bits_fast(data, bits_per_color, pixels_count)

    def _pack_bits_fast(self, data: np.ndarray, bits_per_color: int, total_pixels: int) -> bytes:
        """Упаковка битов для общего случая"""
        bits_mask = (1 << bits_per_color) - 1

        # Вычисляем необходимый размер выходного буфера
        total_bits = total_pixels * bits_per_color
        output_size = (total_bits + 7) // 8
        result = np.zeros(output_size, dtype=np.uint8)

        # Упаковываем биты используя векторные операции
        for i in range(bits_per_color):
            bit_plane = ((data >> i) & 1).astype(np.uint8)
            # Распределяем биты по выходному массиву
            bit_positions = np.arange(total_pixels) * bits_per_color + i
            byte_positions = bit_positions // 8
            bit_offsets = 7 - (bit_positions % 8)  # MSB first
            # Используем np.add.at для аккуратного обновления
            mask = byte_positions < output_size
            np.add.at(result, byte_positions[mask], (bit_plane[mask] << bit_offsets[mask]).astype(np.uint8))

        return result.tobytes()

    def dequantize_from_bytes_to_bytes(self, quantization_data: bytes, width: int, height: int) -> bytes:
        pixels_count = width * height
        bits_per_color = (self.COLORS - 1).bit_length()

        # Быстрая распаковка
        if bits_per_color == 1:
            arr = np.frombuffer(quantization_data, dtype=np.uint8)
            quantized = np.unpackbits(arr)[:pixels_count]
        elif bits_per_color == 2:
            arr = np.frombuffer(quantization_data, dtype=np.uint8)
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
            arr = np.frombuffer(quantization_data, dtype=np.uint8)
            unpacked_size = len(arr) * 2
            unpacked = np.zeros(unpacked_size, dtype=np.uint8)
            unpacked[0::2] = (arr >> 4) & 0xF
            unpacked[1::2] = arr & 0xF
            quantized = unpacked[:pixels_count]
        else:
            quantized = self._unpack_bits_fast(quantization_data, bits_per_color, pixels_count)

        # Деквантование через LUT
        dequantized = self._dequant_lut[quantized]

        # Создаем изображение
        rgb_array = dequantized.reshape(height, width)
        rgb_array = np.stack([rgb_array] * 3, axis=-1)
        return rgb_array.astype(np.uint8).tobytes()

    def dequantize_from_bytes(self, quantization_data: bytes, width: int, height: int) -> Image:
        rgb_bytes = self.dequantize_from_bytes_to_bytes(quantization_data, width, height)
        return Image.frombytes('RGB', (width, height), rgb_bytes)

    def _unpack_bits_fast(self, data: bytes, bits_per_color: int, pixels_count: int) -> np.ndarray:
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

        return result


if __name__ == "__main__":
    input_image = Image.open(r"C:\Users\UserLog.ru\PycharmProjects\regular\basic\image\data\v4.png")

    quant = GrayscaleQuantizerBytes(colors=4)

    from time import time

    # start_time = time()
    gray_quants = quant.quantize_to_bytes(input_image)
    # print("quantize_to_bytes", f"{time() - start_time}s", sep="\t")

    # print(len(gray_quants) // 1024, "KB")

    # start_time = time()
    # _ = quant.dequantize_from_bytes_to_bytes(gray_quants, *input_image.size)
    # print("dequantize_from_bytes", f"{time() - start_time}s", sep="\t")
#
    # start_time = time()
    # result = quant.dequantize_from_bytes(gray_quants, *input_image.size)
    # print("dequantize_from_bytes", f"{time() - start_time}s", sep="\t")
#
    # result.show()
