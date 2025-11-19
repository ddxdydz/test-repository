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

        print(path.name, img_array.shape, img_array.size, f"iterations={iterations}")
        print(str().rjust(20), *[str(bpv).rjust(10, ' ') for bpv in self.BITS_PER_COLORS_LIST],
              "avg".rjust(10, ' '), sep="\t")

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
    from basic.image.quanting.CombQuantizer import CombQuantizer

    img_path = Path(__file__).parent.parent.parent / "data" / "a10.png"
    tester = QuantizerBenchmark()
    tester.test([CombQuantizer(), GrayQuantizer(4), RGBQuantizer(4)], img_path, 100)
    tester.test([CombQuantizer(), GrayQuantizer(4), RGBQuantizer(4)], img_path, 100)


"""
a6.png (480, 640, 3) 921600, iterations=100
                    	         1	         2	         3	         4	         5	         6	         7	         8	       avg
       CombQuantizer
          quant(sec)	  0.008454	  0.010274	  0.008579	  0.010267	  0.008517	  0.010201	  0.008901	  0.010284	0.009435
        dequant(sec)	  0.007355	  0.007058	  0.007277	  0.007080	  0.007244	  0.007172	  0.007107	  0.007057	0.007169
      compress_ratio	  0.041667	  0.083333	  0.125000	  0.166667	  0.208333	  0.250000	  0.291667	  0.333333	0.187500
       GrayQuantizer
          quant(sec)	  0.000450	  0.000448	  0.000449	  0.000447	  0.000450	  0.000448	  0.000445	  0.000450	0.000448
        dequant(sec)	  0.000553	  0.000548	  0.000547	  0.000555	  0.000539	  0.000549	  0.000547	  0.000550	0.000548
      compress_ratio	  0.041667	  0.083333	  0.125000	  0.166667	  0.208333	  0.250000	  0.291667	  0.333333	0.187500
        RGBQuantizer
          quant(sec)	  0.000796	  0.000762	  0.000748	  0.000751	  0.000753	  0.000753	  0.000747	  0.000726	0.000755
        dequant(sec)	  0.000750	  0.000733	  0.000749	  0.000739	  0.000712	  0.000740	  0.000750	  0.000723	0.000737
      compress_ratio	  0.125000	  0.250000	  0.375000	  0.500000	  0.625000	  0.750000	  0.875000	  1.000000	0.562500

a6.png (480, 640, 3) 921600 iterations=100
                    	         1	         2	         3	         4	         5	         6	         7	         8	       avg
       CombQuantizer
          quant(sec)	  0.013841	  0.007833	  0.007839	  0.007748	  0.007805	  0.007707	  0.007911	  0.007976	0.008583
        dequant(sec)	  0.005550	  0.005807	  0.005321	  0.005747	  0.005345	  0.005836	  0.005381	  0.005810	0.005600
      compress_ratio	  0.041667	  0.083333	  0.125000	  0.166667	  0.208333	  0.250000	  0.291667	  0.333333	0.187500
"""
