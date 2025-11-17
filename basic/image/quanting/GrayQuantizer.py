import cv2
import numpy as np

from basic.image.quanting.ABC_Quantizer import Quantizer


class GrayQuantizer(Quantizer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def quantize(self, image: np.ndarray) -> np.ndarray:
        return cv2.LUT(cv2.cvtColor(image, cv2.COLOR_RGB2GRAY), self._quant_lut)

    def dequantize(self, quantized_image: np.ndarray) -> np.ndarray:
        return cv2.cvtColor(cv2.LUT(quantized_image, self._dequant_lut), cv2.COLOR_GRAY2RGB)
