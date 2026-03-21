import cv2
import numpy as np
from PIL import Image


def convert_with_pil_quantize(input_path, output_path):
    # Загрузка и конвертация в RGB
    img = Image.open(input_path).convert('RGB')

    # Квантование до 2 цветов (Pillow сам выбирает метод)
    quantized = img.quantize(colors=2)

    # Конвертация в 1‑битное изображение
    binary = quantized.convert('1')

    # Сохранение с чересстрочной развёрткой
    binary.save(output_path, interlace=1)


# Использование
convert_with_pil_quantize('a8.jpg', 'output.png')
