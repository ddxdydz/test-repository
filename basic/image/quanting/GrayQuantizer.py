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


if __name__ == "__main__":
    from pathlib import Path
    from PIL import Image

    quantizer = GrayQuantizer(4)

    img_path = Path(__file__).parent.parent / "data" / "v4.png"
    original_img = Image.open(img_path)
    img_array = np.array(original_img, dtype=np.uint8)
    Image.fromarray(quantizer.dequantize(quantizer.quantize(img_array))).show()
