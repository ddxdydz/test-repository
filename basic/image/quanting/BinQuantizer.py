import cv2
import numpy as np

from basic.image.quanting.ABC_Quantizer import Quantizer


class BinQuantizer(Quantizer):
    def __init__(self, *args, **kwargs):
        super().__init__(2)

    def quantize(self, image: np.ndarray) -> np.ndarray:
        image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

        # Otsu автоматически находит оптимальный порог
        image = cv2.adaptiveThreshold(
            image,
            255,  # Максимальное значение пикселя при выполнении условия
            cv2.ADAPTIVE_THRESH_MEAN_C,  # Метод: среднее значение окрестности
            cv2.THRESH_BINARY,  # Тип порога: бинаризация
            3,  # Размер окрестности (блок 199×199 пикселей)
            -26  # Константа C, вычитаемая из вычисленного порога
        )

        # image = cv2.blur(image, (2, 2))
        # Структурный элемент для операций (подберите размер под шрифт)
        # kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (4, 4))
        # image = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)  # Удаление мелких точек (шум)
        # image = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)  # Соединение близко расположенных штрихов

        return cv2.LUT(image, self._quant_lut)

    def dequantize(self, quantized_image: np.ndarray) -> np.ndarray:
        return cv2.cvtColor(cv2.LUT(quantized_image, self._dequant_lut), cv2.COLOR_GRAY2RGB)


if __name__ == "__main__":
    from pathlib import Path
    from PIL import Image

    quantizer = BinQuantizer()

    img_path = Path(__file__).parent.parent / "data" / "a10.jpg"
    original_img = Image.open(img_path)
    img_array = np.array(original_img, dtype=np.uint8)
    Image.fromarray(quantizer.dequantize(quantizer.quantize(img_array))).show()
