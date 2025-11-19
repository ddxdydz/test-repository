import threading
from math import ceil

from basic.image.compression.base_compressors import *


class MultiCompressor(Compressor):
    # MAX_CHUNK_LENGTH = 16384
    # MIN_CHUNK_LENGTH = 256
    # OPTIMAL_CHUNK_COUNT = 8
    MAX_CHUNK_LENGTH = 16384
    MIN_CHUNK_LENGTH = 256
    OPTIMAL_CHUNK_COUNT = 14

    BYTES_PER_CHUNK_COUNT = 1
    BYTES_PER_CHUNK_LENGTH = 4
    BYTES_PER_DATA_LENGTH = 4

    def __init__(self):
        super().__init__()
        self.tools = [BZ2Compressor(), ZlibCompressor()]

    @classmethod
    def _calculate_chunk_count(cls, data_length: int) -> int:
        min_chunk_count = ceil(data_length / cls.MAX_CHUNK_LENGTH)
        max_chunk_count = max(1, data_length // cls.MIN_CHUNK_LENGTH)
        if max_chunk_count < cls.OPTIMAL_CHUNK_COUNT:
            return max_chunk_count
        if min_chunk_count < cls.OPTIMAL_CHUNK_COUNT < max_chunk_count:
            return cls.OPTIMAL_CHUNK_COUNT
        return min_chunk_count

    @staticmethod
    def _calculate_chunk_length(data_length: int, chunk_count: int) -> int:
        return ceil(data_length / chunk_count)

    def compress(self, data: bytes) -> bytes:
        if not data:
            return b''

        chunk_count = self._calculate_chunk_count(len(data))
        chunk_length = self._calculate_chunk_length(len(data), chunk_count)

        # Используем списки для потокобезопасного доступа
        nearest_uncompleted_task_index = 0
        uncompleted_task_count = chunk_count
        result_list = [None] * chunk_count  # Фиксированный размер для правильного порядка

        lock = threading.Lock()

        def worker(compressor: Compressor):
            nonlocal nearest_uncompleted_task_index, uncompleted_task_count
            while True:
                # Фиксация задачи
                with lock:
                    if uncompleted_task_count == 0:
                        break
                    task_index = nearest_uncompleted_task_index
                    offset = task_index * chunk_length
                    # Последний чанк может быть меньше
                    if task_index == chunk_count - 1:
                        task = data[offset:]
                    else:
                        task = data[offset:offset + chunk_length]

                # Выполнение задачи
                result = compressor.compress(task)

                # Фиксация результата
                with lock:
                    if nearest_uncompleted_task_index == task_index:
                        nearest_uncompleted_task_index += 1
                        uncompleted_task_count -= 1
                        result_list[task_index] = result

        workers = []
        for tool in self.tools:
            worker_thread = threading.Thread(target=worker, args=(tool,))
            workers.append(worker_thread)
            worker_thread.start()

        for worker_thread in workers:
            worker_thread.join()

        # Проверяем, что все задачи выполнены
        if None in result_list:
            raise RuntimeError("Not all chunks were compressed")

        # Сборка результата
        # header = chunk_count.to_bytes(self.BYTES_PER_CHUNK_COUNT, 'big')
        # header += chunk_length.to_bytes(self.BYTES_PER_CHUNK_LENGTH, 'big')
        # header += len(data).to_bytes(self.BYTES_PER_DATA_LENGTH, 'big')

        # Добавляем размеры каждого сжатого чанка
        # compressed_chunks = result_list
        # chunks_info = b''.join(
        #     [len(chunk).to_bytes(4, 'big') for chunk in compressed_chunks]
        # )

        # return header + chunks_info + b''.join(compressed_chunks)
        return b''.join(result_list)

    def decompress(self, compressed_data: bytes) -> bytes:

        return compressed_data
