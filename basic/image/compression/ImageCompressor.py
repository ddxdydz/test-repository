import bz2
import lzma
import zlib
from abc import ABC, abstractmethod
from enum import Enum
from typing import Tuple, Optional, Dict, Any

from PIL import Image

from basic.image.quanting.GrayscaleQuantizerBytes import GrayscaleQuantizerBytes
from basic.image.quanting.RGBQuantizerBytes import RGBQuantizerBytes


class CompressionAlgorithm(Enum):
    LZMA = 0
    ZLIB = 1
    BZ2 = 2
    NO_COMPRESSION = 3


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


class NoCompressor(BaseCompressor):
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
        compressors = {
            CompressionAlgorithm.LZMA: LZMACompressor(),
            CompressionAlgorithm.ZLIB: ZlibCompressor(),
            CompressionAlgorithm.BZ2: BZ2Compressor(),
            CompressionAlgorithm.NO_COMPRESSION: NoCompressor()
        }
        return compressors[compression]

    @staticmethod
    def _create_quantizer(quantization: Optional[QuantizationMethod], colors_count: int):
        quantizers = {
            QuantizationMethod.GRAYSCALE: GrayscaleQuantizerBytes(colors_count),
            QuantizationMethod.RGB: RGBQuantizerBytes(colors_count),
            QuantizationMethod.NO_QUANTIZATION: None
        }
        return quantizers[quantization]

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


if __name__ == "__main__":
    input_image = Image.open(r"C:\Users\UserLog.ru\PycharmProjects\regular\basic\image\data\v4.png")
    compressor = ImageCompressor(CompressionAlgorithm.LZMA.value, QuantizationMethod.GRAYSCALE.value, 4)
    compress_data, _ = compressor.compress(input_image)
    print(len(compress_data) // 1024, "KB")
    decomp_imp = compressor.decompress(compress_data, input_image.size)
    decomp_imp.show()
