from pathlib import Path

import cv2
from PIL import Image
from time import time
import numpy as np

def bw_pipeline(image_array):
    # Загрузка
    # cv2.imread(input_path, cv2.IMREAD_GRAYSCALE)
    image = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)

    ST = time()
    image = cv2.blur(image, (2, 2))  # 1
    print("1", time() - ST)

    # Адаптивная бинаризация
    ST = time()
    image = cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    print("2", time() - ST)

    return image


img_path = Path(__file__).parent / "basic" / "image" / "data" / 'a9.jpg'


from basic.image.ToolsManager import ToolsManager
tools_manager = ToolsManager(1917, 1079, 3, 60, "bin")
RT, image_array = tools_manager.open()
print(RT)
RT1, image_array = tools_manager.convert(image_array)
print(RT1)
RT1, image_array = tools_manager.quantize(image_array)
print(RT1)
# RT1, image_array = tools_manager.convert(image_array)
# print(RT1)

RT1, image_array = tools_manager.dequantize(image_array)
print(RT1)
# image_array = bw_pipeline(image_array)
Image.fromarray(image_array).show()

# RT1, image_array = tools_manager.pack(result)
# print(RT1)
# RT1, image_array = tools_manager.compress(image_array)
# print(RT1)

print(tools_manager)
print(len(image_array))


