import cv2
import numpy as np


def compress_text_image(input_path, output_path, dpi_target=200):
    """
    Сжимает изображение с текстом с сохранением читаемости.
    """
    # Загрузка
    img = cv2.imread(input_path)

    # Уменьшение разрешения (если нужно)
    height, width = img.shape[:2]
    scale = dpi_target / 300  # предполагаем исходное 300 DPI
    new_size = (int(width * scale), int(height * scale))
    resized = cv2.resize(img, new_size, interpolation=cv2.INTER_AREA)

    # В градации серого
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

    # Адаптивная бинаризация
    binary = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=11,
        C=2
    )

    # Морфологическая очистка
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
    cleaned = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

    # Сохранение в BMP (1 бит/пиксель)
    cv2.imwrite(output_path, cleaned)
    print(f"Сохранено: {output_path}")


# Использование
compress_text_image('a8.jpg', 'output.bmp')
