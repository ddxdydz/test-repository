import bz2
import lzma
import zlib
from abc import ABC, abstractmethod
from enum import Enum
from time import time
from typing import Tuple, Optional, Dict, Any

import numpy as np
from PIL import Image


class BaseQuantizer(ABC):
    """Абстрактный базовый класс для квантователей"""

    def __init__(self, colors=3):
        if not (1 < colors < 257):
            raise ValueError("Number of colors must be between 1 and 256")
        self.COLORS = colors

    def value_to_quant(self, value: int) -> int:
        """Convert pixel value (0-255) to quantization level"""
        if self.COLORS == 1:
            return 0
        return min(value // (256 // self.COLORS), self.COLORS - 1)

    def quant_to_value(self, quant: int) -> int:
        """Convert quantization level back to pixel value (0-255)"""
        if not 0 <= quant < self.COLORS:
            raise ValueError(f"Quant level must be between 0 and {self.COLORS - 1}")

        if self.COLORS == 1:
            return 255

        return int((quant * 255) / (self.COLORS - 1))

    @abstractmethod
    def quantize(self, img: Image) -> [int]:
        """Абстрактный метод для квантования изображения"""
        pass

    @abstractmethod
    def dequantize(self, quantize_data: bytes, width: int, height: int) -> [int]:
        """Абстрактный метод для восстановления изображения"""
        pass


class GrayscaleQuantizer(BaseQuantizer):
    """Квантователь в оттенки серого"""

    def quantize(self, img: Image) -> [int]:
        """Квантование в оттенки серого"""
        if img.mode != 'RGB':
            img = img.convert('RGB')

        width, height = img.size
        pixels_data = img.load()
        quants = []

        for row in range(height):
            for col in range(width):
                r, g, b = pixels_data[col, row]
                # Используем средневзвешенное значение для лучшего восприятия
                brightness = int(0.299 * r + 0.587 * g + 0.114 * b)
                quants.append(self.value_to_quant(brightness))

        return quants

    def dequantize(self, quants: [int], width: int, height: int) -> Image:
        """Восстановление черно-белого изображения"""
        if len(quants) != width * height:
            raise ValueError("Quants array size doesn't match image dimensions")

        img = Image.new('RGB', (width, height))
        pixels_data = img.load()

        index = 0
        for row in range(height):
            for col in range(width):
                quant_val = quants[index]
                pixel_value = self.quant_to_value(quant_val)
                pixels_data[col, row] = (pixel_value, pixel_value, pixel_value)
                index += 1

        return img


class GrayscaleQuantizerBytes(GrayscaleQuantizer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Предвычисляем LUT для максимальной скорости
        self._quant_lut = np.array([self.value_to_quant(i) for i in range(256)], dtype=np.uint8)
        self._dequant_lut = np.array([self.quant_to_value(i) for i in range(self.COLORS)], dtype=np.uint8)

    def quantize_to_bytes(self, img: Image) -> bytes:
        if img.mode != 'RGB':
            img = img.convert('RGB')

        arr = np.array(img, dtype=np.uint8)
        width, height = img.size
        pixels_count = width * height

        # Супербыстрое вычисление яркости и квантование через LUT
        brightness = np.dot(arr, [0.299, 0.587, 0.114]).astype(np.uint8)
        quantized = self._quant_lut[brightness.flatten()]

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


class RGBQuantizer(BaseQuantizer):
    """Квантователь для цветных RGB изображений"""

    def __init__(self, colors_per_channel=3):
        """
        Инициализация RGB квантователя

        Args:
            colors_per_channel: количество цветов на каждый канал (R, G, B)
        """
        super().__init__(colors_per_channel)
        self.total_colors = colors_per_channel ** 3

    def quantize(self, img: Image, return_single_array: bool = False):
        """
        Квантование RGB изображения

        Args:
            return_single_array: если True, возвращает упакованный массив
        """
        if img.mode != 'RGB':
            img = img.convert('RGB')

        width, height = img.size
        pixels_data = img.load()

        if return_single_array:
            return self._quantize_to_single_array(width, height, pixels_data)
        else:
            return self._quantize_to_tuples(width, height, pixels_data)

    def _quantize_to_tuples(self, width, height, pixels_data) -> [tuple]:
        """Квантование в кортежи (r, g, b)"""
        quantized_pixels = []
        for row in range(height):
            for col in range(width):
                r, g, b = pixels_data[col, row]
                r_quant = self.value_to_quant(r)
                g_quant = self.value_to_quant(g)
                b_quant = self.value_to_quant(b)
                quantized_pixels.append((r_quant, g_quant, b_quant))
        return quantized_pixels

    def _quantize_to_single_array(self, width, height, pixels_data) -> [int]:
        """Квантование в упакованный массив"""
        single_array = []
        for row in range(height):
            for col in range(width):
                r, g, b = pixels_data[col, row]
                r_quant = self.value_to_quant(r)
                g_quant = self.value_to_quant(g)
                b_quant = self.value_to_quant(b)
                # Упаковываем три значения в одно число
                pixel_value = (r_quant * (self.COLORS ** 2) +
                               g_quant * self.COLORS +
                               b_quant)
                single_array.append(pixel_value)
        return single_array

    def dequantize(self, quantized_data, width: int, height: int) -> Image:
        """
        Восстановление изображения из квантованных данных

        Args:
            quantized_data: может быть списком кортежей или упакованным массивом
        """
        if len(quantized_data) != width * height:
            raise ValueError("Quantized data size doesn't match image dimensions")

        # Определяем тип данных
        is_single_array = False if isinstance(quantized_data[0], tuple) else True
        return self._dequantize(quantized_data, width, height, is_single_array)

    def _dequantize(self, quantized_data, width, height, is_single_array: bool = False) -> Image:
        img = Image.new('RGB', (width, height))
        pixels_data = img.load()

        index = 0
        for row in range(height):
            for col in range(width):
                if is_single_array:
                    packed_value = quantized_data[index]
                    # Распаковываем значения
                    r_quant = packed_value // (self.COLORS ** 2)
                    remainder = packed_value % (self.COLORS ** 2)
                    g_quant = remainder // self.COLORS
                    b_quant = remainder % self.COLORS
                else:
                    r_quant, g_quant, b_quant = quantized_data[index]
                r_val = self.quant_to_value(r_quant)
                g_val = self.quant_to_value(g_quant)
                b_val = self.quant_to_value(b_quant)
                pixels_data[col, row] = (r_val, g_val, b_val)
                index += 1

        return img

    def quantize_to_bytes(self, img: Image) -> bytes:
        ...

    def dequantize_from_bytes(self, quantize_data: bytes, width: int, height: int) -> Image:
        ...

    def get_color_palette(self) -> list:
        """Получение полной RGB палитры"""
        palette = []
        for r in range(self.COLORS):
            for g in range(self.COLORS):
                for b in range(self.COLORS):
                    palette.append((
                        self.quant_to_value(r),
                        self.quant_to_value(g),
                        self.quant_to_value(b)
                    ))
        return palette

    @staticmethod
    def get_compression_ratio(original_img: Image, use_single_array: bool = True) -> float:
        """Коэффициент сжатия для RGB"""
        original_size = original_img.width * original_img.height * 3  # 3 байта на пиксель

        if use_single_array:
            quantized_size = original_img.width * original_img.height  # 1 число на пиксель
        else:
            quantized_size = original_img.width * original_img.height * 3  # 3 числа на пиксель

        return original_size / quantized_size


class RGBQuantizerBytes(RGBQuantizer):
    def quantize_to_bytes(self, img: Image) -> bytes:
        if img.mode != 'RGB':
            img = img.convert('RGB')

        width, height = img.size
        pixels_data = img.load()

        bits_per_color = self.total_colors.bit_length()
        if bits_per_color == 0 or bits_per_color > 8:  # TODO
            raise ValueError("Невозможно преобразовать в bytes, уменьшите количество цветов для quantization.")

        # Предвычисление констант
        bits_mask = (1 << bits_per_color) - 1
        result = bytearray()
        # Обработка по 8 байт за раз для лучшей производительности
        current_byte = 0
        bits_used = 0
        # Используем локальные переменные для скорости
        append = result.append

        for row in range(height):
            for col in range(width):

                r, g, b = pixels_data[col, row]
                r_quant = self.value_to_quant(r)
                g_quant = self.value_to_quant(g)
                b_quant = self.value_to_quant(b)
                color = (r_quant * (self.COLORS ** 2) + g_quant * self.COLORS + b_quant)

                # Действия с битами
                current_byte = (current_byte << bits_per_color) | (color & bits_mask)
                bits_used += bits_per_color
                if bits_used >= 8:
                    append(current_byte >> (bits_used - 8))
                    bits_used -= 8
                    # Маска для оставшихся битов
                    current_byte &= (1 << bits_used) - 1

        # Обработка остатка
        if bits_used > 0:
            append(current_byte << (8 - bits_used))

        return bytes(result)

    def dequantize_from_bytes(self, quantization_data: bytes, width: int, height: int) -> Image:
        img = Image.new('RGB', (width, height))
        pixels_data = img.load()
        pixels_count = width * height

        bits_per_color = self.total_colors.bit_length()
        if bits_per_color == 0 or bits_per_color > 8:
            raise ValueError("Некорректная битовая глубина в данных (должно быть 1 байт на цвет)")

        # Предвычисление констант
        bits_mask = (1 << bits_per_color) - 1

        # Используем локальные переменные для скорости
        current_buffer = 0
        current_bits = 0

        color_index = 0

        for byte_val in quantization_data:
            current_buffer = (current_buffer << 8) | byte_val
            current_bits += 8

            # Извлекаем все возможные цвета из текущего буфера
            while current_bits >= bits_per_color:
                shift = current_bits - bits_per_color
                quant_value = (current_buffer >> shift) & bits_mask

                r_quant = quant_value // (self.COLORS ** 2)
                remainder = quant_value % (self.COLORS ** 2)
                g_quant = remainder // self.COLORS
                b_quant = remainder % self.COLORS
                r = self.quant_to_value(r_quant)
                g = self.quant_to_value(g_quant)
                b = self.quant_to_value(b_quant)

                row = color_index // width
                col = color_index % width
                pixels_data[col, row] = (r, g, b)
                color_index += 1
                if color_index == pixels_count:
                    break

                current_buffer &= (1 << shift) - 1
                current_bits -= bits_per_color

        return img

    def dequantize_from_bytes_to_bytes(self, quantization_data: bytes, width: int, height: int) -> bytes:
        return self.dequantize_from_bytes(quantization_data, width, height).tobytes()


class CompressionAlgorithm(Enum):
    LZMA = 0
    ZLIB = 1
    BZ2 = 2
    RAW = 3


class QuantizationMethod(Enum):
    GRAYSCALE = 0
    RGB = 1
    NO_QUANTIZATION = 2


class BaseCompressor(ABC):
    """Базовый класс для компрессоров"""

    def __init__(self):
        self.name = self.__class__.__name__

    @abstractmethod
    def compress(self, data: bytes) -> bytes:
        pass

    @abstractmethod
    def decompress(self, compressed_data: bytes) -> bytes:
        pass


class LZMACompressor(BaseCompressor):
    def compress(self, data: bytes) -> bytes:
        return lzma.compress(data, preset=9)

    def decompress(self, compressed_data: bytes) -> bytes:
        return lzma.decompress(compressed_data)


class ZlibCompressor(BaseCompressor):
    def __init__(self, level: int = 9):
        super().__init__()
        self.level = level

    def compress(self, data: bytes) -> bytes:
        return zlib.compress(data, level=self.level)

    def decompress(self, compressed_data: bytes) -> bytes:
        return zlib.decompress(compressed_data)


class BZ2Compressor(BaseCompressor):
    def __init__(self, level: int = 9):
        super().__init__()
        self.level = level

    def compress(self, data: bytes) -> bytes:
        return bz2.compress(data, compresslevel=self.level)

    def decompress(self, compressed_data: bytes) -> bytes:
        return bz2.decompress(compressed_data)


class RawCompressor(BaseCompressor):
    """Компрессор без сжатия (для сравнения)"""

    def compress(self, data: bytes) -> bytes:
        return data

    def decompress(self, compressed_data: bytes) -> bytes:
        return compressed_data


class ImageCompressor:
    def __init__(self, compression: int, quantization: int, colors_count: int = 8):
        self.compression_algorithm = CompressionAlgorithm(compression)
        self.quantization_method = QuantizationMethod(quantization)
        self.colors_count = colors_count
        self.parameters = compression, quantization, colors_count
        self.compressor = self._create_compressor(self.compression_algorithm)
        self.quantizer = self._create_quantizer(self.quantization_method, colors_count)

    @staticmethod
    def get_img_mode(quantization: QuantizationMethod):
        if quantization == QuantizationMethod.GRAYSCALE:
            return 'L'
        return 'RGB'

    @staticmethod
    def _create_compressor(compression: CompressionAlgorithm) -> BaseCompressor:
        """Создание компрессора на основе алгоритма"""
        compressors = {
            CompressionAlgorithm.LZMA: LZMACompressor(),
            CompressionAlgorithm.ZLIB: ZlibCompressor(),
            CompressionAlgorithm.BZ2: BZ2Compressor(),
            CompressionAlgorithm.RAW: RawCompressor()
        }
        return compressors[compression]

    @staticmethod
    def _create_quantizer(quantization: Optional[QuantizationMethod], colors_count: int):
        """Создание квантователя"""
        if quantization == QuantizationMethod.GRAYSCALE:
            return GrayscaleQuantizerBytes(colors_count)
        elif quantization == QuantizationMethod.RGB:
            return RGBQuantizerBytes(colors_count)
        else:
            return None

    def get_info(self) -> Tuple:
        """Получение информации о настройках компрессора"""
        return (self.compression_algorithm.value,
                self.quantization_method.value,
                self.colors_count)

    def compress(self, img: Image) -> Tuple[bytes, Dict[str, Any]]:
        """Сжатие изображения"""

        # Применение квантования
        if self.quantization_method == QuantizationMethod.NO_QUANTIZATION:
            # Без квантования - обычное преобразование в байты
            img_mode = self.get_img_mode(self.quantization_method)
            if img.mode != img_mode:
                img = img.convert(img_mode)
            img_bytes = img.tobytes()
        else:
            img_bytes = self.quantizer.quantize_to_bytes(img)

        # Сжатие данных
        compressed_data = self.compressor.compress(img_bytes)

        return compressed_data, {'size': img.size, 'compressor_parameters': self.get_info()}

    def decompress(self, compressed_data: bytes, img_size: Tuple[int, int]) -> Image:
        """Декомпрессия изображения"""
        decompressed_bytes = self.compressor.decompress(compressed_data)

        # Восстановление изображения
        if self.quantization_method == QuantizationMethod.NO_QUANTIZATION:
            return Image.frombytes(
                self.get_img_mode(self.quantization_method),
                img_size,
                decompressed_bytes
            )

        return self.quantizer.dequantize_from_bytes(decompressed_bytes, *img_size)

    def decompress_to_bytes(self, compressed_data: bytes, img_size: Tuple[int, int]) -> bytes:
        """Декомпрессия изображения"""
        decompressed_bytes = self.compressor.decompress(compressed_data)
        if self.quantization_method == QuantizationMethod.NO_QUANTIZATION:
            return decompressed_bytes
        return self.quantizer.dequantize_from_bytes_to_bytes(decompressed_bytes, *img_size)


class ImageCompressorLZMAGS4(ImageCompressor):
    def __init__(self):
        super().__init__(CompressionAlgorithm.LZMA.value, QuantizationMethod.GRAYSCALE.value, 4)


if __name__ == "__main__":
    input_image = Image.open(r"C:\Users\UserLog.ru\PycharmProjects\regular\basic\image\data\v4.png")

    compressor = ImageCompressorLZMAGS4()

    time_start11 = time()
    compress_data, _ = compressor.compress(input_image)
    total_compress = time() - time_start11
    print("total_compress", f"{total_compress}s", sep="\t")

    print(len(compress_data) // 1024, "KB")

    time_start22 = time()
    decomp_imp = compressor.decompress(compress_data, input_image.size)
    total_decompress = time() - time_start22
    print("total_decompress", f"{total_decompress}s", sep="\t")

    print("total", "\t", total_compress + total_decompress)

    decomp_imp.show()
