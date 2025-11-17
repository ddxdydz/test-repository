import cv2
import numpy as np

from basic.image.quanting.ABC_Quantizer import Quantizer
from basic.image.quanting.tools.generate_palette import generate_palette


class CombQuantizer(Quantizer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._palette = generate_palette(self.COLORS)  # [(r: int, g: int, b: int), ...]

        self._quant_lut = np.array([self._value_to_quant(i) for i in range(256)], dtype=np.uint8)
        self._dequant_lut = np.array(
            [self._quant_to_value(min(i, self.COLORS - 1)) for i in range(256)], dtype=np.uint8)

    def quantize(self, image: np.ndarray) -> np.ndarray:
        return cv2.LUT(cv2.cvtColor(image, cv2.COLOR_RGB2GRAY), self._quant_lut)

    def dequantize(self, quantized_image: np.ndarray) -> np.ndarray:
        return cv2.cvtColor(cv2.LUT(quantized_image, self._dequant_lut), cv2.COLOR_GRAY2RGB)


if __name__ == "__main__":
    quantizer = CombQuantizer()

    # img_path = Path(__file__).parent.parent / "data" / "v4.png"
    # original_img = Image.open(img_path)
    # img_array = np.array(original_img, dtype=np.uint8)
    # Image.fromarray(quantizer.dequantize(quantizer.quantize(img_array))).show()
