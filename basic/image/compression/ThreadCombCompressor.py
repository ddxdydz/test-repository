import threading
from math import ceil
from typing import List, Optional

from basic.image.compression.base_compressors import *


class ThreadCombCompressor(Compressor):
    BYTES_PER_CHUNK_COUNT = 1
    BYTES_PER_CHUNK_LENGTH = 4
    BYTES_PER_CHUNK_INDEX = 1

    MAX_CHUNK_LENGTH = 16384
    MIN_CHUNK_LENGTH = 256
    OPTIMAL_CHUNK_COUNT = 14

    def __init__(self, compressors: Optional[List[Compressor]] = None):
        super().__init__()
        if compressors is None:
            self.compressors = [BZ2Compressor(), ZlibCompressor()]
        else:
            self.compressors = compressors

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
        tool_index_list = [0] * chunk_count

        lock = threading.Lock()

        def worker(compressor: Compressor, index):
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
                        tool_index_list[task_index] = index

        workers = []
        tool_index = 0
        for tool in self.compressors:
            worker_thread = threading.Thread(target=worker, args=(tool, tool_index))
            workers.append(worker_thread)
            worker_thread.start()
            tool_index += 1

        for worker_thread in workers:
            worker_thread.join()

        if None in result_list:
            raise RuntimeError("Not all chunks were compressed")

        header_chunk_count = chunk_count.to_bytes(self.BYTES_PER_CHUNK_COUNT, 'big')
        indexes_info = b''.join(
            i.to_bytes(self.BYTES_PER_CHUNK_INDEX, 'big') for i in tool_index_list
        )
        chunks_length_info = b''.join(
            len(chunk).to_bytes(self.BYTES_PER_CHUNK_LENGTH, 'big') for chunk in result_list
        )

        return header_chunk_count + indexes_info + chunks_length_info + b''.join(result_list)

    def decompress(self, compressed_data: bytes) -> bytes:
        if not compressed_data:
            return b''

        chunk_count = int.from_bytes(compressed_data[:self.BYTES_PER_CHUNK_COUNT], 'big')
        offset = self.BYTES_PER_CHUNK_COUNT

        compressors_indexes = []
        for _ in range(chunk_count):
            compressor_index = int.from_bytes(compressed_data[offset:offset + self.BYTES_PER_CHUNK_INDEX], 'big')
            compressors_indexes.append(compressor_index)
            offset += self.BYTES_PER_CHUNK_INDEX

        chunk_lengths = []
        for _ in range(chunk_count):
            chunk_length = int.from_bytes(compressed_data[offset:offset + self.BYTES_PER_CHUNK_LENGTH], 'big')
            chunk_lengths.append(chunk_length)
            offset += self.BYTES_PER_CHUNK_LENGTH

        decompressed_chunks = []
        for i in range(chunk_count):
            compressor_index = compressors_indexes[i]
            chunk_length = chunk_lengths[i]
            chunk_data = compressed_data[offset:offset + chunk_length]
            decompressed_chunks.append(self.compressors[compressor_index].decompress(chunk_data))
            offset += chunk_length

        return b''.join(decompressed_chunks)
