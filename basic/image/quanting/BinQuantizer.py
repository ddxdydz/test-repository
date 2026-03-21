import cv2
import numpy as np

from .ABC_Quantizer import Quantizer


class BinQuantizer(Quantizer):
    def __init__(self, *args, **kwargs):
        super().__init__(2)

    def quantize(self, image: np.ndarray) -> np.ndarray:
        image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

        # Otsu автоматически находит оптимальный порог
        _, image = cv2.threshold(
            image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )

        # image = cv2.blur(image, (2, 2))

        return cv2.LUT(image, self._quant_lut)

    def dequantize(self, quantized_image: np.ndarray) -> np.ndarray:
        return cv2.cvtColor(cv2.LUT(quantized_image, self._dequant_lut), cv2.COLOR_GRAY2RGB)


if __name__ == "__main__":
    from pathlib import Path
    from PIL import Image

    quantizer = GrayQuantizer(3)

    img_path = Path(__file__).parent.parent / "data" / "g2.jpg"
    original_img = Image.open(img_path)
    img_array = np.array(original_img, dtype=np.uint8)
    Image.fromarray(quantizer.dequantize(quantizer.quantize(img_array))).show()
