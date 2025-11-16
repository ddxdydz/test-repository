import cv2
import numpy as np
from PIL import Image

from basic.image.IMGArray import IMGArray
from basic.image.quanting.ABC_Quantizer import Quantizer
from basic.image.quanting.tools.pack_image import pack_image
from basic.image.quanting.tools.unpack_image import unpack_image


class GrayQuantizer(Quantizer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def quantize(self, image: IMGArray) -> np.ndarray:
        return cv2.LUT(cv2.cvtColor(image.array, cv2.COLOR_RGB2GRAY), self._quant_lut)

    def dequantize(self, quantized_image: np.ndarray) -> IMGArray:
        return IMGArray(numpy_array=cv2.cvtColor(cv2.LUT(quantized_image, self._dequant_lut), cv2.COLOR_GRAY2RGB))

    def pack_quantized(self, quantized_image: np.ndarray) -> bytes:
        return pack_image(quantized_image.flatten(), self.bits_per_color, quantized_image.size)

    def unpack_quantized(self, data: bytes, image_width: int, image_height: int) -> np.ndarray:
        return unpack_image(data, self.bits_per_color, image_width * image_height).reshape(image_height, image_width)


if __name__ == "__main__":
    original_img = IMGArray(Image.open(r"C:\Users\UserLog.ru\PycharmProjects\regular\basic\image\data\v10.png"))
    quantizer = GrayQuantizer(colors=4)
    iterations = 1000
    height, width, _ = original_img.shape

    from time import time

    total_quantize_time = 0
    total_packing_time = 0
    for _ in range(iterations):
        start_time = time()
        quantized = quantizer.quantize(original_img)
        total_quantize_time += time() - start_time
        start_time = time()
        quantizer.pack_quantized(quantized)
        total_packing_time += time() - start_time
    quantize_time = total_quantize_time / iterations
    packing_time = total_packing_time / iterations
    print("quantize_to_bytes", f"{quantize_time + packing_time:.4f}s = quantize_time({quantize_time:.4f}) + " +
                               f"packing_time({packing_time:.4f})", sep="\t")

    total_dequantize_time = 0
    total_unpacking_time = 0
    packed_quantized = quantizer.pack_quantized(quantizer.quantize(original_img))
    for _ in range(iterations):
        start_time = time()
        unpacked = quantizer.unpack_quantized(packed_quantized, width, height)
        total_unpacking_time += time() - start_time
        start_time = time()
        quantizer.dequantize(unpacked)
        total_dequantize_time += time() - start_time
    dequantize_time = total_dequantize_time / iterations
    unpacking_time = total_unpacking_time / iterations
    print("dequantize_to_bytes", f"{dequantize_time + unpacking_time:.4f}s = " +
          f"dequantize_time({dequantize_time:.4f}) + " +
          f"unpacking_time({unpacking_time:.4f})", sep="\t")

    print(len(packed_quantized) // 1024, "KB")
    quantizer.dequantize(quantizer.unpack_quantized(packed_quantized, width, height)).show()

"""
v4
quantize_to_bytes	0.0170s = quantize_time(0.0068) + packing_time(0.0101)
dequantize_to_bytes	0.0170s = dequantize_time(0.0078) + unpacking_time(0.0092)
504 KB

v10
quantize_to_bytes	0.0020s = quantize_time(0.0009) + packing_time(0.0012)
dequantize_to_bytes	0.0017s = dequantize_time(0.0005) + unpacking_time(0.0012)
75 KB

original_imgarray = np.array(Image.open(v10.png))
quantizer = GrayQuantizer(colors=4)
iterations = 1000
quantize_to_bytes	0.0017s = quantize_time(0.0007) + packing_time(0.0010)
dequantize_to_bytes	0.0016s = dequantize_time(0.0004) + unpacking_time(0.0012)
75 KB
"""
