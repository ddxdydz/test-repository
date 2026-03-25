from time import time
from basic.image.compression.base_compressors import *


class AdaptiveCompressor(Compressor):
    """Компрессор с адаптивным выбором алгоритма сжатия."""
    BYTES_PER_INDEX = 1

    TEST_DATA_SIZE = 1024  # Размер тестовых данных
    MIN_DATA_FOR_TESTING = TEST_DATA_SIZE * 16  # Минимальный размер для тестирования

    TEST_PART = 0.2

    def __init__(self):
        super().__init__()
        self.compressors = [BZ2Compressor(), ZlibCompressor()]

    def _select_test_data(self, data: bytes) -> bytes:
        """Выбирает репрезентативные данные для тестирования."""
        if len(data) <= self.TEST_DATA_SIZE:
            return data

        # Берем данные из начала, середины и конца для лучшего покрытия
        chunk_size = self.TEST_DATA_SIZE // 3
        start_chunk = data[:chunk_size]
        middle_chunk = data[len(data) // 2 - chunk_size // 2: len(data) // 2 + chunk_size // 2]
        end_chunk = data[-chunk_size:]

        return start_chunk + middle_chunk + end_chunk

    def compress(self, data: bytes) -> bytes:
        if not data:
            return b''

        if len(data) < self.MIN_DATA_FOR_TESTING:
            return self.compressors[0].compress(data)

        # data_for_test = self._select_test_data_by_part(data)

        step = int(len(data) // len(data) * self.TEST_PART)
        if step < 4:
            return self.compressors[0].compress(data)
        data_for_test = data[::step]

        time_results = []
        for compressor in self.compressors:
            _start_time = time()
            compressor.compress(data_for_test)
            time_results.append(time() - _start_time)
        chosen_compressor_index = min(range(len(self.compressors)), key=lambda i: time_results[i])

        header = chosen_compressor_index.to_bytes(self.BYTES_PER_INDEX, 'big')

        return header + self.compressors[chosen_compressor_index].compress(data)

    def decompress(self, compressed_data: bytes) -> bytes:
        chosen_compressor_index = int.from_bytes(compressed_data[:self.BYTES_PER_INDEX], 'big')
        return self.compressors[chosen_compressor_index].compress(compressed_data[self.BYTES_PER_INDEX:])
