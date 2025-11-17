import cv2
import numpy as np
from PIL import Image

from basic.image.quanting.ABC_Quantizer import Quantizer


class RGBQuantizer(Quantizer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def quantize(self, image: np.ndarray) -> np.ndarray:
        return cv2.LUT(image, self._quant_lut)

    def dequantize(self, quantized_image: np.ndarray) -> np.ndarray:
        return cv2.LUT(quantized_image, self._dequant_lut)


if __name__ == "__main__":
    from time import time
    from pathlib import Path

    img_path = Path(__file__).parent.parent / "data" / "v10.png"
    original_img = Image.open(img_path)
    img_array = np.array(original_img, dtype=np.uint8)
    colors = 4
    quantizer = RGBQuantizer(colors=colors)
    iterations = 1000
    height, width, _ = img_array.shape

    total_quantize_time = 0
    total_dequantize_time = 0
    for _ in range(iterations):
        start_time = time()
        quantized = quantizer.quantize(img_array)
        total_quantize_time += time() - start_time
        start_time = time()
        quantizer.dequantize(quantized)
        total_dequantize_time += time() - start_time
    quantize_time = total_quantize_time / iterations
    dequantize_time = total_dequantize_time / iterations

    print(f"{quantizer}, path={img_path.name}")
    print("quantize_to_bytes", f"{quantize_time:.4f}s")
    print("dequantize_to_bytes", f"{dequantize_time:.4f}s")
