import threading
from math import ceil
from typing import List, Optional

from basic.image.compression.base_compressors import *


class ThreadCompressor(Compressor):
    BYTES_PER_CHUNK_COUNT = 1
    BYTES_PER_CHUNK_LENGTH = 4

    MIN_CHUNK_LENGTH = 8192
    MIN_DATA_FOR_TESTING = MIN_CHUNK_LENGTH * 2

    def __init__(self, compressors: Optional[List[Compressor]] = None):
        super().__init__()
        if compressors is None:
            self.compressors = [BZ2Compressor(), BZ2Compressor()]
        else:
            self.compressors = compressors

    def compress(self, data: bytes) -> bytes:
        if not data:
            return b''

        if len(data) < self.MIN_DATA_FOR_TESTING:
            return int(1).to_bytes(self.BYTES_PER_CHUNK_COUNT, 'big') + self.compressors[0].compress(data)

        chunk_count = len(self.compressors)
        chunk_length = ceil(len(data) / chunk_count)
        result_list = [None] * chunk_count
        lock = threading.Lock()

        def worker(compressor: Compressor, chunk_index: int):
            with lock:
                offset = chunk_index * chunk_length
                if chunk_index == chunk_count - 1:  # Последний чанк может быть меньше
                    task = data[offset:]
                else:
                    task = data[offset:offset + chunk_length]
            result = compressor.compress(task)
            with lock:
                result_list[chunk_index] = result

        workers = []
        for i in range(chunk_count):
            worker_thread = threading.Thread(target=worker, args=(self.compressors[i], i))
            workers.append(worker_thread)
            worker_thread.start()

        for worker_thread in workers:
            worker_thread.join()

        if None in result_list:
            raise RuntimeError("Not all chunks were compressed")

        header_chunk_count = chunk_count.to_bytes(self.BYTES_PER_CHUNK_COUNT, 'big')
        chunks_length_info = b''.join(
            len(chunk).to_bytes(self.BYTES_PER_CHUNK_LENGTH, 'big') for chunk in result_list
        )

        return header_chunk_count + chunks_length_info + b''.join(result_list)

    def decompress(self, compressed_data: bytes) -> bytes:
        if not compressed_data:
            return b''
        chunk_count = int.from_bytes(compressed_data[:self.BYTES_PER_CHUNK_COUNT], 'big')
        offset = self.BYTES_PER_CHUNK_COUNT

        chunk_lengths = []
        for _ in range(chunk_count):
            chunk_length = int.from_bytes(compressed_data[offset:offset + self.BYTES_PER_CHUNK_LENGTH], 'big')
            chunk_lengths.append(chunk_length)
            offset += self.BYTES_PER_CHUNK_LENGTH

        decompressed_chunks = []
        for i in range(chunk_count):
            chunk_length = chunk_lengths[i]
            chunk_data = compressed_data[offset:offset + chunk_length]
            decompressed_chunks.append(self.compressors[0].decompress(chunk_data))
            offset += chunk_length

        return b''.join(decompressed_chunks)
