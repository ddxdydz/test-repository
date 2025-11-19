from time import perf_counter
from basic.image.compression.base_compressors import *


class AdaptiveCompressor(Compressor):
    """Компрессор с адаптивным выбором алгоритма сжатия."""

    TEST_DATA_SIZE = 1024  # Размер тестовых данных
    MIN_DATA_FOR_TESTING = TEST_DATA_SIZE * 2  # Минимальный размер для тестирования

    def __init__(self):
        super().__init__()
        self.compressors = [BZ2Compressor(), ZlibCompressor()]
        self._last_choice = 0  # Для отслеживания выбора

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

    def _benchmark_compressors(self, test_data: bytes) -> int:
        """Сравнивает компрессоры и возвращает индекс лучшего."""
        best_compressor_idx = 0
        best_score = float('inf')

        for i, compressor in enumerate(self.compressors):
            try:
                start_time = perf_counter()
                compressed = compressor.compress(test_data)
                compression_time = perf_counter() - start_time

                # Оценка: учитываем и скорость, и эффективность сжатия
                compression_ratio = len(compressed) / len(test_data)

                # Комбинированная оценка (можно настроить веса)
                score = compression_ratio * 0.7 + compression_time * 0.3

                if score < best_score:
                    best_score = score
                    best_compressor_idx = i

            except Exception:
                # Если компрессор не справился, пробуем следующий
                continue

        return best_compressor_idx

    def compress(self, data: bytes) -> bytes:
        if not data:
            return b''

        # Для маленьких данных используем компрессор по умолчанию
        if len(data) < self.MIN_DATA_FOR_TESTING:
            compressed = self.compressors[0].compress(data)
            self._last_choice = 0
            return compressed

        # Выбираем лучший компрессор на основе тестовых данных
        test_data = self._select_test_data(data)
        best_compressor_idx = self._benchmark_compressors(test_data)

        # Используем выбранный компрессор для всех данных
        compressed = self.compressors[best_compressor_idx].compress(data)
        self._last_choice = best_compressor_idx

        return compressed

    def get_compressor_info(self) -> dict:
        """Возвращает информацию о последнем использованном компрессоре."""
        return {
            'chosen_compressor': self._last_choice,
            'available_compressors': [type(comp).__name__ for comp in self.compressors]
        }

    def decompress(self, compressed_data: bytes) -> bytes:
        return b''
