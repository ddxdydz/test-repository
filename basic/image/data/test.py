import cv2
from PIL import Image
from time import time
import numpy as np


def bw_pipeline(input_path, output_path):
    # Загрузка
    image = cv2.imread(input_path, cv2.IMREAD_GRAYSCALE)

    ST = time()
    image = cv2.blur(image, (2, 2))  # 1
    print("1", time() - ST)

    # Адаптивная бинаризация
    ST = time()
    image = cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    print("2", time() - ST)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    image = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)
    # image = cv2.medianBlur(image, ksize=1)

    # Сохранение
    cv2.imwrite(output_path, image)

    return image

result = bw_pipeline('a10.jpg', 'test4_final_output.jpg')
print(result)
Image.fromarray(result).show()
