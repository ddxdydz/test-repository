import cv2
import numpy as np

from basic.image.quanting.ABC_Quantizer import Quantizer


class RGBQuantizer(Quantizer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def quantize(self, image: np.ndarray) -> np.ndarray:
        return cv2.LUT(image, self._quant_lut)

    def dequantize(self, quantized_image: np.ndarray) -> np.ndarray:
        return cv2.LUT(quantized_image, self._dequant_lut)
