import bz2
import lzma
import zlib
from abc import ABC, abstractmethod
from enum import Enum
from typing import Tuple, Optional, Dict, Any

from PIL import Image

from basic.image.quanting.GrayscaleQuantizerBytes import GrayscaleQuantizerBytes
from basic.image.quanting.RGBQuantizerBytes import RGBQuantizerBytes
from time import time


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
    def __init__(self, compression: CompressionAlgorithm,
                 quantization: Optional[QuantizationMethod] = None,
                 colors_count: int = 8):
        self.compression_algorithm = compression
        self.quantization_method = quantization
        self.colors_count = colors_count
        self.compressor = self._create_compressor(compression)
        self.quantizer = self._create_quantizer(quantization, colors_count)

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
        return (self.compression_algorithm,
                self.quantization_method,
                self.colors_count)

    def compress(self, img: Image) -> Tuple[bytes, Dict[str, Any]]:
        """Сжатие изображения"""

        # Применение квантования

        time_start = time()

        if self.quantization_method == QuantizationMethod.NO_QUANTIZATION:
            # Без квантования - обычное преобразование в байты
            img_mode = self.get_img_mode(self.quantization_method)
            if img.mode != img_mode:
                img = img.convert(img_mode)
            img_bytes = img.tobytes()
        else:
            img_bytes = self.quantizer.quantize_to_bytes(img)

        print("quantization", f"{time() - time_start}s", sep="\t")

        # Сжатие данных
        time_start = time()

        compressed_data = self.compressor.compress(img_bytes)

        print("compress", f"{time() - time_start}s", sep="\t")

        return compressed_data, {'size': img.size, 'compressor_parameters': self.get_info()}

    def decompress(self, compressed_data: bytes, img_size: Tuple[int, int]) -> Image:
        """Декомпрессия изображения"""

        time_start = time()
        decompressed_bytes = self.compressor.decompress(compressed_data)
        print("decompress", f"{time() - time_start}s", sep="\t")

        # Восстановление изображения
        if self.quantization_method == QuantizationMethod.NO_QUANTIZATION:
            return Image.frombytes(
                self.get_img_mode(self.quantization_method),
                img_size,
                decompressed_bytes
            )

        time_start = time()
        res = self.quantizer.dequantize_from_bytes(decompressed_bytes, *img_size)
        print("quantization", f"{time() - time_start}s", sep="\t")

        return res


if __name__ == "__main__":
    input_image = Image.open(r"C:\Users\UserLog.ru\PycharmProjects\regular\basic\image\data\v4.png")

    compressor = ImageCompressor(CompressionAlgorithm.LZMA, QuantizationMethod.GRAYSCALE, 4)
    time_start11 = time()
    compress_data, _ = compressor.compress(input_image)
    print("total compress", f"{time() - time_start11}s", sep="\t")

    print(len(compress_data) // 1024, "KB")

    # compressor = LZMACompressor()
    # time_start11 = time()
    # compress_data = compressor.compress(compress_data)
    # print("BZ2Compressor", f"{time() - time_start11}s", sep="\t")
    # print(len(compress_data) // 1024, "KB")

    # time_start22 = time()
    # decomp_imp = compressor.decompress(compress_data, input_image.size)
    # print("total decompress", f"{time() - time_start22}s", sep="\t")
    # decomp_imp.show()
