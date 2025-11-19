import concurrent.futures

from basic.image.compression.ChunkWrapper import ChunkWrapper
from basic.image.compression.base_compressors import *


class CombCompressor(Compressor):
    PULL_SIZE = 4

    def __init__(self):
        super().__init__()
        self.compressors = [BZ2Compressor(), ZlibCompressor(), LZMACompressor()]

    def compress(self, data: bytes) -> bytes:
        # Используем ProcessPoolExecutor для настоящего параллелизма
        with concurrent.futures.ProcessPoolExecutor(max_workers=len(self.compressors)) as executor:
            future_to_compressor = {
                executor.submit(compressor.compress, data): compressor
                for compressor in self.compressors
            }

            try:
                for future in concurrent.futures.as_completed(future_to_compressor.keys()):
                    try:
                        result = future.result()
                        # Отмена в процессах работает лучше
                        for other_future in future_to_compressor.keys():
                            if not other_future.done():
                                other_future.cancel()
                        return result
                    except Exception:
                        continue
                return data
            except Exception:
                return data

    def _compress_single(self, compressor, data):
        return compressor.compress(data)

    def decompress(self, compressed_data: bytes) -> bytes:
        ...

        return compressed_data
