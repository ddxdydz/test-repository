import cv2
import numpy as np

from basic.image.resizing.ABC_ImageResizer import ImageResizer, ResizeMethod


class CVResizer(ImageResizer):
    """Версия с использованием OpenCV для максимальной скорости"""
    _CV_INTERPOLATION_MAP = {
        ResizeMethod.NEAREST: cv2.INTER_NEAREST,
        ResizeMethod.BILINEAR: cv2.INTER_LINEAR,
        ResizeMethod.BICUBIC: cv2.INTER_CUBIC,
        ResizeMethod.LANCZOS: cv2.INTER_LANCZOS4,
        ResizeMethod.AREA: cv2.INTER_AREA
    }

    def __init__(self, scale: float = 0.6, method: ResizeMethod | int = ResizeMethod.LANCZOS,
                 original_size: tuple[int, int] | None = None):
        super().__init__(scale, method, original_size)

    def _basic_resize(self, image: np.array, target_size: tuple[int, int]) -> np.array:
        return cv2.resize(image, target_size, interpolation=CVResizer._CV_INTERPOLATION_MAP[self.method])


if __name__ == "__main__":
    from pathlib import Path
    from basic.image.resizing.test.TestResizer import TestResizer
    image_path = Path(__file__).parent.parent / "data" / "v10.png"
    test_pil = TestResizer(CVResizer(scale=0.6), image_path, 100)
    test_pil.DATA_PATH = image_path
    test_pil.test()

"""
CVResizer(scale=0.6, method=LANCZOS): 0.36
NEAREST   		resize_time=0.000322 c		desize_time=0.000553 c
AREA      		resize_time=0.001532 c		desize_time=0.000592 c
BILINEAR  		resize_time=0.000382 c		desize_time=0.000588 c
BICUBIC   		resize_time=0.000468 c		desize_time=0.001032 c
LANCZOS   		resize_time=0.003511 c		desize_time=0.003169 c
"""
