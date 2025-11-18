from pathlib import Path
from time import time
from typing import List
import numpy as np
from basic.image.compression.compressors import Compressor


class CompressorBenchmark:
    TEST_DATA_WEIGHTS = (1024, 2048, 4096, 4096 * 2, 4096 * 4, 4096 * 8)

    def __init__(self):
        self._test_data_cache = {}

    def _generate_test_data(self, data_weight: int) -> bytes:
        """Генерирует тестовые данные для сжатия"""
        cache_key = data_weight
        if cache_key not in self._test_data_cache:
            # Генерируем случайные данные заданного размера
            data = np.random.bytes(data_weight)
            self._test_data_cache[cache_key] = data
        return self._test_data_cache[cache_key]

    @staticmethod
    def _test_compress(compressor: Compressor, data: bytes, iterations: int) -> float:
        """Тестирует скорость сжатия"""
        compress_times = []
        for _ in range(iterations):
            start_time = time()
            compressor.compress(data)
            compress_times.append(time() - start_time)
        return float(np.mean(compress_times))

    @staticmethod
    def _test_decompress(compressor: Compressor, data: bytes, iterations: int) -> float:
        """Тестирует скорость распаковки"""
        decompress_times = []
        compressed = compressor.compress(data)
        for _ in range(iterations):
            start_time = time()
            compressor.decompress(compressed)
            decompress_times.append(time() - start_time)
        return float(np.mean(decompress_times))

    @staticmethod
    def _get_compress_ratio(compressor: Compressor, data: bytes) -> float:
        """Вычисляет коэффициент сжатия"""
        compressed = compressor.compress(data)
        return len(compressed) / len(data)

    def test(self, compressors: List[Compressor], data: bytes, iterations: int = 100):
        """Запускает тестирование компрессоров"""
        print(f"iterations={iterations}, test_data: {len(data) // 1024} KB = {len(data)} B")
        # print("".rjust(20), *[str(w).rjust(10, ' ') for w in self.TEST_DATA_WEIGHTS],
        #       "avg".rjust(10, ' '), sep="\t")

        for compressor in compressors:
            print(compressor.name.rjust(20))

            # Тестирование сжатия
            print(f"compress(sec)".rjust(20), end="\t")
            compress_times = []
            for weight in self.TEST_DATA_WEIGHTS:
                # test_data = self._generate_test_data(weight)
                compress_time = self._test_compress(compressor, data, iterations)
                compress_times.append(compress_time)
                print(f"{compress_time:.6f}".rjust(10), end="\t")
            print(f"\t{float(np.mean(compress_times)):.6f}")

            # Тестирование распаковки
            print(f"decompress(sec)".rjust(20), end="\t")
            decompress_times = []
            for weight in self.TEST_DATA_WEIGHTS:
                # test_data = self._generate_test_data(weight)
                decompress_time = self._test_decompress(compressor, data, iterations)
                decompress_times.append(decompress_time)
                print(f"{decompress_time:.6f}".rjust(10), end="\t")
            print(f"\t{float(np.mean(decompress_times)):.6f}")

            # Тестирование коэффициента сжатия
            print(f"compress_ratio".rjust(20), end="\t")
            compress_ratios = []
            for weight in self.TEST_DATA_WEIGHTS:
                # test_data = self._generate_test_data(weight)
                compress_ratio = self._get_compress_ratio(compressor, data)
                compress_ratios.append(compress_ratio)
                print(f"{compress_ratio:.6f}".rjust(10), end="\t")
            print(f"\t{float(np.mean(compress_ratios)):.6f}")


if __name__ == "__main__":
    from basic.image.compression.compressors import *

    from PIL import Image
    from basic.image.quanting.GrayQuantizer import GrayQuantizer
    from basic.image.packing.CombPacker import CombPacker
    img_path = Path(__file__).parent.parent.parent / "data" / "v4.png"
    original_img = Image.open(img_path)
    img_array = np.array(original_img, dtype=np.uint8)
    quantizer = GrayQuantizer(4)
    # packer = CombPacker(quantizer.bits_per_color)
    # test_data = packer.pack_array(quantizer.quantize(img_array))
    packer = CombPacker(8)
    test_data = packer.pack_array(img_array)

    tester = CompressorBenchmark()
    tester.test([ZlibCompressor(), LZMACompressor(), BZ2Compressor(), GzipCompressor()], test_data, 10)

"""
iterations=10, test_data: 504 KB = 517116 B
      ZlibCompressor
       compress(sec)	  0.196457	  0.194119	  0.194369	  0.193847	  0.193428	  0.193910		0.194355
     decompress(sec)	  0.001604	  0.001552	  0.001551	  0.001577	  0.001621	  0.001606		0.001585
      compress_ratio	  0.089674	  0.089674	  0.089674	  0.089674	  0.089674	  0.089674		0.089674
      LZMACompressor
       compress(sec)	  0.195815	  0.192732	  0.190319	  0.191532	  0.192732	  0.191966		0.192516
     decompress(sec)	  0.005374	  0.005494	  0.005470	  0.005412	  0.005444	  0.005421		0.005436
      compress_ratio	  0.073129	  0.073129	  0.073129	  0.073129	  0.073129	  0.073129		0.073129
       BZ2Compressor
       compress(sec)	  0.015836	  0.015817	  0.015826	  0.015868	  0.015750	  0.015749		0.015808
     decompress(sec)	  0.007488	  0.007397	  0.007475	  0.007400	  0.007514	  0.007272		0.007424
      compress_ratio	  0.079143	  0.079143	  0.079143	  0.079143	  0.079143	  0.079143		0.079143
      GzipCompressor
       compress(sec)	  0.194084	  0.193827	  0.195080	  0.194533	  0.196087	  0.193671		0.194547
     decompress(sec)	  0.001706	  0.001706	  0.001704	  0.001704	  0.001706	  0.001657		0.001697
      compress_ratio	  0.089697	  0.089697	  0.089697	  0.089697	  0.089697	  0.089697		0.089697

iterations=10, test_data: 8079 KB = 8273779 B
      ZlibCompressor
       compress(sec)	  0.362514	  0.358445	  0.357936	  0.359514	  0.357814	  0.346476		0.357117
     decompress(sec)	  0.029311	  0.029655	  0.028964	  0.028483	  0.028938	  0.030422		0.029296
      compress_ratio	  0.096584	  0.096584	  0.096584	  0.096584	  0.096584	  0.096584		0.096584
      LZMACompressor
       compress(sec)	  1.272463	  1.248255	  1.241261	  1.254762	  1.244030	  1.261881		1.253775
     decompress(sec)	  0.091661	  0.088680	  0.090671	  0.088429	  0.088293	  0.087660		0.089232
      compress_ratio	  0.059825	  0.059825	  0.059825	  0.059825	  0.059825	  0.059825		0.059825
       BZ2Compressor
       compress(sec)	  3.094016	  3.169658	  3.117835	  3.165758	  3.086790	  3.224848		3.143151
     decompress(sec)	  0.261368	  0.257313	  0.258620	  0.267212	  0.257282	  0.261096		0.260482
      compress_ratio	  0.076172	  0.076172	  0.076172	  0.076172	  0.076172	  0.076172		0.076172
      GzipCompressor
       compress(sec)	  0.378693	  0.382890	  0.374867	  0.376103	  0.378387	  0.378712		0.378275
     decompress(sec)	  0.034290	  0.033767	  0.032073	  0.033554	  0.033330	  0.032337		0.033225
      compress_ratio	  0.096585	  0.096585	  0.096585	  0.096585	  0.096585	  0.096585		0.096585

256 MB
bz2 compress 79.99023222923279
bz2 decompress 5.219536066055298
10 KB
lzma compress 12.713189363479614
lzma decompress 1.9897534847259521
38 KB
zlib compress 3.7556722164154053
zlib decompress 0.733863115310669
382 KB
"""
