import cv2
import numpy as np
from PIL import Image

from basic.image.resizing.ABC_ImageResizer import ImageResizer, ResizeMethod


class CVResizer(ImageResizer):
    """Версия с использованием OpenCV для максимальной скорости"""
    def __init__(self, scale: float = 0.6, method: ResizeMethod | int = ResizeMethod.LANCZOS,
                 original_size: tuple[int, int] | None = None):
        super().__init__(scale, method, original_size)

    def _basic_resize(self, image: Image.Image, target_size: tuple[int, int]) -> Image.Image:
        # Конвертируем PIL в OpenCV формат
        cv_image = np.array(image)

        resized = cv2.resize(cv_image, target_size,
                             interpolation=cv2.INTER_LINEAR)

        return Image.fromarray(resized)


if __name__ == "__main__":
    from pathlib import Path
    image_path = Path(__file__).parent.parent / "data" / "v10.png"
    input_image = Image.open(image_path)

    from basic.image.resizing.test.TestResizer import TestResizer
    test_pil = TestResizer(CVResizer(scale=0.6), image_path, 20)
    test_pil.DATA_PATH = image_path
    test_pil.ITERATION_COUNT = 1
    test_pil.test()

"""
CVResizer(scale=0.6, method=LANCZOS): 36.00%
NEAREST   		resize_time=0.00613 c		desize_time=0.00445 c
AREA      		resize_time=0.004296 c		desize_time=0.004356 c
BILINEAR  		resize_time=0.00419 c		desize_time=0.004272 c
BICUBIC   		resize_time=0.004057 c		desize_time=0.004136 c
LANCZOS   		resize_time=0.004327 c		desize_time=0.004309 c
"""
