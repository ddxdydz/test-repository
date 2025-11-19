from math import ceil
from concurrent.futures import ThreadPoolExecutor
from typing import List
from basic.image.compression.base_compressors import *


class ChunkWrapper(Compressor):
    MAX_CHUNK_COUNT = 4
    MIN_CHUNK_LENGTH = 4096
    BYTES_PER_CHUNK_COUNT = 1
    BYTES_PER_CHUNK_LENGTH = 4
    BYTES_PER_DATA_LENGTH = 4

    def __init__(self, compressor: Compressor = ZlibCompressor(), max_workers: int = 4):
        super().__init__()
        self.name = f"CW({compressor.name})"
        self.compressor = compressor
        self.max_workers = max_workers

    @classmethod
    def _calculate_optimal_chunk_params(cls, data_length: int) -> tuple[int, int]:
        """Вычисляет оптимальное количество и размер чанков"""
        if data_length <= cls.MIN_CHUNK_LENGTH:
            return 1, data_length

        # Пытаемся найти баланс между количеством чанков и их размером
        for chunk_count in range(cls.MAX_CHUNK_COUNT, 0, -1):
            chunk_length = ceil(data_length / chunk_count)
            if chunk_length >= cls.MIN_CHUNK_LENGTH:
                return chunk_count, chunk_length

        # Если не нашли - используем максимальное количество чанков
        return cls.MAX_CHUNK_COUNT, ceil(data_length / cls.MAX_CHUNK_COUNT)

    def _split_into_chunks(self, data: bytes, chunk_length: int) -> List[bytes]:
        """Разбивает данные на чанки"""
        return [data[i:i + chunk_length] for i in range(0, len(data), chunk_length)]

    def _compress_chunk(self, chunk: bytes) -> bytes:
        """Сжимает один чанк"""
        return self.compressor.compress(chunk)

    def compress(self, data: bytes) -> bytes:
        if not data:
            return b''

        chunk_count, chunk_length = self._calculate_optimal_chunk_params(len(data))
        chunks = self._split_into_chunks(data, chunk_length)

        # Параллельное сжатие чанков
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            compressed_chunks = list(executor.map(self._compress_chunk, chunks))

        # Сборка результата
        header = chunk_count.to_bytes(self.BYTES_PER_CHUNK_COUNT, 'big')
        header += chunk_length.to_bytes(self.BYTES_PER_CHUNK_LENGTH, 'big')
        header += len(data).to_bytes(self.BYTES_PER_DATA_LENGTH, 'big')

        # Добавляем размеры каждого сжатого чанка
        chunks_info = b''.join(
            len(chunk).to_bytes(4, 'big') for chunk in compressed_chunks
        )

        return header + chunks_info + b''.join(compressed_chunks)

    def decompress(self, compressed_data: bytes) -> bytes:
        if not compressed_data:
            return b''

        # Парсинг заголовка
        chunk_count = int.from_bytes(compressed_data[:self.BYTES_PER_CHUNK_COUNT], 'big')
        data_length_offset = self.BYTES_PER_CHUNK_COUNT + self.BYTES_PER_CHUNK_LENGTH
        chunk_length = int.from_bytes(compressed_data[self.BYTES_PER_CHUNK_COUNT:data_length_offset],'big')
        data_length = int.from_bytes(
            compressed_data[data_length_offset: data_length_offset + self.BYTES_PER_DATA_LENGTH], 'big')

        offset = self.BYTES_PER_CHUNK_COUNT + self.BYTES_PER_CHUNK_LENGTH + self.BYTES_PER_DATA_LENGTH

        # Чтение информации о размерах чанков
        chunk_sizes = []
        for _ in range(chunk_count):
            chunk_size = int.from_bytes(compressed_data[offset:offset + 4], 'big')
            chunk_sizes.append(chunk_size)
            offset += 4

        # Извлечение и распаковка чанков
        decompressed_chunks = []
        for chunk_size in chunk_sizes:
            chunk_data = compressed_data[offset:offset + chunk_size]
            decompressed_chunks.append(self.compressor.decompress(chunk_data))
            offset += chunk_size

        return b''.join(decompressed_chunks)[:data_length]
