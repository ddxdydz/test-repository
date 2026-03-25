import bz2
import gzip
import lzma
import zlib

from basic.image.compression.ABC_Compressor import Compressor


class LZMACompressor(Compressor):
    def compress(self, data: bytes) -> bytes:
        return lzma.compress(data, preset=9)

    def decompress(self, compressed_data: bytes) -> bytes:
        return lzma.decompress(compressed_data)


class ZlibCompressor(Compressor):
    def __init__(self, level: int = 9):
        super().__init__()
        self.level = level

    def compress(self, data: bytes) -> bytes:
        return zlib.compress(data, level=self.level)

    def decompress(self, compressed_data: bytes) -> bytes:
        return zlib.decompress(compressed_data)


class BZ2Compressor(Compressor):
    def __init__(self, level: int = 9):
        super().__init__()
        self.level = level

    def compress(self, data: bytes) -> bytes:
        return bz2.compress(data, compresslevel=self.level)

    def decompress(self, compressed_data: bytes) -> bytes:
        return bz2.decompress(compressed_data)


class GzipCompressor(Compressor):
    def __init__(self, level: int = 9):
        super().__init__()
        self.level = level

    def compress(self, data: bytes) -> bytes:
        return gzip.compress(data, compresslevel=self.level)

    def decompress(self, compressed_data: bytes) -> bytes:
        return gzip.decompress(compressed_data)
