from pathlib import Path
from time import time
from typing import List

import numpy as np
from PIL import Image

from basic.image.quanting.ABC_Quantizer import Quantizer


class QuantizerBenchmark:
    BITS_PER_COLORS_LIST = list(range(1, 9))

    @staticmethod
    def _test_quantize(quantizer: Quantizer, img_array: np.array, iterations) -> float:
        quantize_times = []
        for _ in range(iterations):
            start_time = time()
            quantizer.quantize(img_array)
            quantize_times.append(time() - start_time)
        return float(np.mean(quantize_times))

    @staticmethod
    def _test_dequantize(quantizer: Quantizer, img_array: np.array, iterations) -> float:
        dequantize_times = []
        quantized = quantizer.quantize(img_array)
        for _ in range(iterations):
            start_time = time()
            quantizer.dequantize(quantized)
            dequantize_times.append(time() - start_time)
        return float(np.mean(dequantize_times))

    @staticmethod
    def _get_compress_ratio(quantizer: Quantizer, img_array: np.array):
        quantized = quantizer.quantize(img_array)
        return (quantized.size * quantizer.bits_per_color) / (img_array.size * 8)

    def test(self, quantizers: List[Quantizer], path: Path, iterations=100):
        original_img = Image.open(path)
        img_array = np.array(original_img, dtype=np.uint8)

        print(path.name, img_array.shape, img_array.size)
        print(str().rjust(20), *[str(bpv).rjust(10, ' ') for bpv in self.BITS_PER_COLORS_LIST], sep="\t")

        for quantizer in quantizers:

            print(quantizer.name.rjust(20))

            # Quantization
            print(f"quant(sec)".rjust(20), end="\t")
            quantize_times = []
            for bits_per_color in self.BITS_PER_COLORS_LIST:
                quantizer.set_colors(2 ** bits_per_color)
                quantize_time = self._test_quantize(quantizer, img_array, iterations)
                quantize_times.append(quantize_time)
                print(f"{quantize_time:.6f}".rjust(10), end="\t")
            print(f"{float(np.mean(quantize_times)):.6f}")

            # Dequantization
            print(f"dequant(sec)".rjust(20), end="\t")
            dequantize_times = []
            for bits_per_color in self.BITS_PER_COLORS_LIST:
                quantizer.set_colors(2 ** bits_per_color)
                dequantize_time = self._test_dequantize(quantizer, img_array, iterations)
                dequantize_times.append(dequantize_time)
                print(f"{dequantize_time:.6f}".rjust(10), end="\t")
            print(f"{float(np.mean(dequantize_times)):.6f}")

            # Compress
            print(f"compress_ratio".rjust(20), end="\t")
            compress_ratios = []
            for bits_per_color in self.BITS_PER_COLORS_LIST:
                quantizer.set_colors(2 ** bits_per_color)
                compress_ratio = self._get_compress_ratio(quantizer, img_array)
                compress_ratios.append(compress_ratio)
                print(f"{compress_ratio:.6f}".rjust(10), end="\t")
            print(f"{float(np.mean(compress_ratios)):.6f}")


if __name__ == "__main__":
    from basic.image.quanting.GrayQuantizer import GrayQuantizer
    from basic.image.quanting.RGBQuantizer import RGBQuantizer

    img_path = Path(__file__).parent.parent.parent / "data" / "v10.png"
    tester = QuantizerBenchmark()
    tester.test([GrayQuantizer(4), RGBQuantizer(4)], img_path, 1000)
