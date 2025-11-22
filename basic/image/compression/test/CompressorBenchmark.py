from math import inf
from pathlib import Path
from time import time

import numpy as np
from PIL import Image

from basic.image.__all_tools import *


class CompressorBenchmark:
    def __init__(self, image_path: Path):
        self.image_path = image_path
        self.image = Image.open(image_path)
        self.image_array = np.array(self.image, dtype=np.uint8)
        self.cache = dict()

    def _prepare(self, input_scale: int, input_colors: int) -> bytes:
        if (input_scale, input_colors) not in self.cache.keys():
            resizer = CVResizerIntScale(input_scale)
            quantizer = GrayQuantizer(input_colors)
            packer = NoTampingPacker(quantizer.bits_per_color)
            resized = resizer.resize(self.image_array)
            quantized = quantizer.quantize(resized)
            self.cache[(input_scale, input_colors)] = packer.pack_array(quantized)
        return self.cache[(input_scale, input_colors)]

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

    def _print_table(self, func, cells_description: str = "None",
                     range_scale: tuple = (40, 100, 10),
                     range_color: tuple = (3, 37, 1),
                     col_width: int = 6):
        print("IMAGE PATH:", self.image_path)
        print("IMAGE SHAPE AND SIZE:", self.image_array.shape, self.image_array.size)
        print(f"IMAGE WEIGHT RANGE: {len(self._prepare(range_scale[0], range_color[0]))} - " +
              f"{len(self._prepare(range_scale[1] - 1, range_color[1] - 1))}", "B")
        print("ROWS/COLS: SCALE_PERCENT/COLORS_COUNT_FOR_QUANTING")
        print(f"CELLS: {cells_description}")
        print(f"{str().ljust(col_width)}{''.join([f"{c}".ljust(col_width) for c in range(*range_color)])}")
        for scale in range(*range_scale):
            print(str(scale).ljust(col_width), end="")
            for colors in range(*range_color):
                print(f"{func(scale, colors)}".ljust(col_width), end="")
            print()

    @staticmethod
    def print_line():
        print("########################################################")

    def print_data_weight_table(self):
        def func(input_scale: int, input_colors: int):
            return len(self._prepare(input_scale, input_colors))
        self._print_table(func=func, cells_description="WEIGHT in Bytes", col_width=8)

    def print_compress_ratio_table(self, compressor: Compressor):
        def func(input_scale: int, input_colors: int):
            prepared = self._prepare(input_scale, input_colors)
            return f"{int(self._get_compress_ratio(compressor, prepared) * 100)}"
        print(f"COMPRESSOR: {compressor.name}")
        self._print_table(func=func, cells_description="compress ratio in %", col_width=6)

    def print_compress_time_table(self, compressor: Compressor):
        def func(input_scale: int, input_colors: int):
            prepared = self._prepare(input_scale, input_colors)
            compress_time = self._test_compress(compressor, prepared, 1)
            return f"{int(compress_time * 1000)}"
        print(f"COMPRESSOR: {compressor.name}")
        self._print_table(func=func, cells_description="compression time in ms", col_width=6)

    def print_decompress_time_table(self, compressor: Compressor):
        def func(input_scale: int, input_colors: int):
            prepared = compressor.compress(self._prepare(input_scale, input_colors))
            decompress_time = self._test_decompress(compressor, prepared, 1)
            return f"{int(decompress_time * 1000)}"
        print(f"COMPRESSOR: {compressor.name}")
        self._print_table(func=func, cells_description="decompression time in ms", col_width=8)

    def print_compress_ratio_comparison_table(self, compressor1: Compressor, compressor2: Compressor):
        def func(input_scale: int, input_colors: int):
            prepared = self._prepare(input_scale, input_colors)
            ratio1 = self._get_compress_ratio(compressor1, prepared)
            ratio2 = self._get_compress_ratio(compressor2, prepared)
            if ratio1 < 0.01 and ratio2 < 0.01:
                ratio = 1
            elif not ratio2 > 0:
                ratio = inf
            else:
                ratio = ratio1 / ratio2
            return f"{ratio:.1f}"
        print(f"COMPRESSOR1: {compressor1.name}, COMPRESSOR2: {compressor2.name}")
        self._print_table(func=func, cells_description="ratio = compress_1_ratio / compress_2_ratio", col_width=6)

    def print_compress_time_comparison_table(self, compressor1: Compressor, compressor2: Compressor):
        def func(input_scale: int, input_colors: int):
            prepared = self._prepare(input_scale, input_colors)
            time1 = self._test_compress(compressor1, prepared, 1)
            time2 = self._test_compress(compressor2, prepared, 2)
            if time1 < 0.01 and time2 < 0.01:
                ratio = 1
            elif not time2 > 0:
                ratio = inf
            else:
                ratio = time1 / time2
            return f"{ratio:.1f}"
        print(f"COMPRESSOR1: {compressor1.name}, COMPRESSOR2: {compressor2.name}")
        self._print_table(func=func, cells_description="ratio = compress_1_time / compress_2_time", col_width=6)


if __name__ == "__main__":
    # for img_name in ["a2.jpg", "a3.jpg", "a4.jpg", "a5.jpg", "a6.jpg", "a7.jpg", "a8.jpg", "a9.jpg", "a10.jpg",
    #                  "g1.jpg", "g2.jpg"]:
    #     benchmark = CompressorBenchmark(Path(__file__).parent.parent.parent / "data" / img_name)
    #     benchmark.print_line()
    #     benchmark.print_data_weight_table()
    #     benchmark.print_compress_ratio_table(BZ2Compressor())
    #     benchmark.print_compress_time_table(BZ2Compressor())
    #     benchmark.print_decompress_time_table(BZ2Compressor())
    #     benchmark.print_compress_time_comparison_table(BZ2Compressor(), ZlibCompressor())
    #     benchmark.print_compress_time_comparison_table(BZ2Compressor(), LZMACompressor())

    # benchmark = CompressorBenchmark(Path(__file__).parent.parent.parent / "data" / "a7.jpg")
    # benchmark.print_compress_time_table(BZ2Compressor())
    # benchmark.print_compress_time_table(ZlibCompressor())
    # benchmark.print_compress_time_table(LZMACompressor())
    # benchmark.print_compress_ratio_table(BZ2Compressor())
    # benchmark.print_compress_ratio_table(ZlibCompressor())
    # benchmark.print_compress_ratio_table(LZMACompressor())

    benchmark = CompressorBenchmark(Path(__file__).parent.parent.parent / "data" / "a7.jpg")
    print(benchmark._test_compress(BZ2Compressor(), benchmark._prepare(60, 4), 1))
    print(benchmark._test_compress(ThreadCompressor(), benchmark._prepare(60, 4), 1))
