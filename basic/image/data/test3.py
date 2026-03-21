import cv2
import numpy as np
from PIL import Image


def quantize_auto_otsu(image_path):
    image = cv2.imread(image_path)
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    gray_image = cv2.blur(gray_image, (2, 2))

    # Otsu автоматически находит оптимальный порог
    _, binary_image = cv2.threshold(
        gray_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    return binary_image


# Использование
result = quantize_auto_otsu('ch1.jpg')
print(result)
Image.fromarray(result).show()
