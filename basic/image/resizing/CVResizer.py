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
