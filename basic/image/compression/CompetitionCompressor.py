import threading

from basic.image.compression.base_compressors import *


class CompetitionCompressor(Compressor):
    BYTES_PER_INDEX = 1

    def __init__(self):
        super().__init__()
        self.compressors = [BZ2Compressor(), ZlibCompressor()]

    def compress(self, data: bytes) -> bytes:
        if not data:
            return b''

        self.compressors = [BZ2Compressor(), ZlibCompressor()]

        result = None
        result_ready = threading.Event()
        lock = threading.Lock()

        def worker(compressor: Compressor, index):
            nonlocal result
            while True:
                compressed = compressor.compress(data)
                with lock:
                    if not result_ready.is_set():
                        result = index.to_bytes(self.BYTES_PER_INDEX, 'big') + compressed
                        result_ready.set()

        workers = []
        tool_index = 0
        for tool in self.compressors:
            worker_thread = threading.Thread(target=worker, args=(tool, tool_index))
            workers.append(worker_thread)
            worker_thread.start()
            tool_index += 1

        result_ready.wait(timeout=10)

        if result is None:
            raise RuntimeError("result is None")

        return result

    def decompress(self, compressed_data: bytes) -> bytes:
        chosen_compressor_index = int.from_bytes(compressed_data[:self.BYTES_PER_INDEX], 'big')
        return self.compressors[chosen_compressor_index].compress(compressed_data[self.BYTES_PER_INDEX:])
