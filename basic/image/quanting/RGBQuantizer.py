import cv2
import numpy as np
from PIL import Image

from basic.image.quanting.ABC_Quantizer import Quantizer
from basic.image.quanting.tools.pack_image import pack_image
from basic.image.quanting.tools.unpack_image import unpack_image


class RGBQuantizer(Quantizer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def quantize(self, image: np.ndarray) -> np.ndarray:
        return cv2.LUT(image, self._quant_lut)

    def dequantize(self, quantized_image: np.ndarray) -> np.ndarray:
        return cv2.LUT(image, self._dequant_lut)

    def pack_quantized(self, quantized_image: np.ndarray) -> bytes:
        return pack_image(quantized_image.flatten(), self.bits_per_color, quantized_image.size)

    def unpack_quantized(self, data: bytes, image_width: int, image_height: int) -> np.ndarray:
        return unpack_image(data, self.bits_per_color, image_width * image_height * 3).reshape(
            image_height, image_width, 3)


if __name__ == "__main__":
    original_imgarray = np.array(Image.open(r"C:\Users\UserLog.ru\PycharmProjects\regular\basic\image\data\v10.png"))
    height, width, _ = original_imgarray.shape
    quantizer = RGBQuantizer(colors=4)
    Image.fromarray(quantizer.dequantize(quantizer.quantize(original_imgarray))).show()
    iterations = 1000

    from time import time

    total_quantize_time = 0
    total_packing_time = 0
    total_dequantize_time = 0
    total_unpacking_time = 0
    packed_quantized = quantizer.pack_quantized(quantizer.quantize(original_imgarray))
    for _ in range(iterations):
        start_time = time()
        quantized = quantizer.quantize(original_imgarray)
        total_quantize_time += time() - start_time
        start_time = time()
        packed = quantizer.pack_quantized(quantized)
        total_packing_time += time() - start_time
        start_time = time()
        unpacked = quantizer.unpack_quantized(packed_quantized, width, height)
        total_unpacking_time += time() - start_time
        start_time = time()
        quantizer.dequantize(unpacked)
        total_dequantize_time += time() - start_time
    quantize_time = total_quantize_time / iterations
    packing_time = total_packing_time / iterations
    dequantize_time = total_dequantize_time / iterations
    unpacking_time = total_unpacking_time / iterations
    print("quantize_to_bytes", f"{quantize_time + packing_time:.4f}s = quantize_time({quantize_time:.4f}) + " +
                               f"packing_time({packing_time:.4f})", sep="\t")
    print("dequantize_to_bytes", f"{dequantize_time + unpacking_time:.4f}s = " +
          f"dequantize_time({dequantize_time:.4f}) + " +
          f"unpacking_time({unpacking_time:.4f})", sep="\t")
    print(len(packed_quantized) // 1024, "KB")

    Image.fromarray(quantizer.dequantize(quantizer.unpack_quantized(packed_quantized, width, height))).show()

"""
v4
quantize_to_bytes	0.0170s = quantize_time(0.0068) + packing_time(0.0101)
dequantize_to_bytes	0.0170s = dequantize_time(0.0078) + unpacking_time(0.0092)
504 KB

v10
quantize_to_bytes	0.0020s = quantize_time(0.0009) + packing_time(0.0012)
dequantize_to_bytes	0.0017s = dequantize_time(0.0005) + unpacking_time(0.0012)
75 KB

quantize_to_bytes	0.0036s = quantize_time(0.0008) + packing_time(0.0028)
dequantize_to_bytes	0.0037s = dequantize_time(0.0009) + unpacking_time(0.0028)
225 KB
"""
