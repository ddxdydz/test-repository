from time import time
from basic.image.compression.base_compressors import *


class TryCompressor(Compressor):
    TEST_DATA_WEIGHT = 1024
    MAX_DATA_WEIGHT_WITHOUT_TEST = TEST_DATA_WEIGHT * 4

    def __init__(self):
        super().__init__()
        self.tools = [BZ2Compressor(), ZlibCompressor()]

    def compress(self, data: bytes) -> bytes:
        if not data:
            return b''

        if len(data) < self.MAX_DATA_WEIGHT_WITHOUT_TEST:
            return self.tools[0].compress(data)

        step = len(data) // self.TEST_DATA_WEIGHT

        data_for_test = data[::step]

        _start_time = time()
        self.tools[0].compress(data_for_test)
        time1 = time() - _start_time

        _start_time = time()
        self.tools[1].compress(data_for_test)
        time2 = time() - _start_time

        if time1 < time2:
            return self.tools[0].compress(data)
        return self.tools[1].compress(data)

    def decompress(self, compressed_data: bytes) -> bytes:

        return compressed_data
