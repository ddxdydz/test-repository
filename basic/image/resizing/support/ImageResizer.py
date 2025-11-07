from PIL import Image

from basic.image.resizing.support.ResizeMethod import ResizeMethod
from basic.image.resizing.support.ResizeTask import ResizeTask


class ImageResizer:
    """Базовый класс для изменения размера изображения"""

    def __init__(self, method: ResizeMethod = ResizeMethod.BILINEAR):
        self.method = method

    def resize(self, image: Image.Image, resize_task: ResizeTask) -> Image.Image:
        """Базовый метод изменения размера"""
        raise NotImplementedError("Метод должен быть реализован в дочернем классе")

    def _get_pil_resample(self) -> int:
        """Получаем метод ресемплинга для PIL"""
        method_map = {
            ResizeMethod.NEAREST: Image.NEAREST,
            ResizeMethod.BILINEAR: Image.BILINEAR,
            ResizeMethod.BICUBIC: Image.BICUBIC,
            ResizeMethod.LANCZOS: Image.LANCZOS,
            ResizeMethod.AREA: Image.BOX
        }
        return method_map[self.method]

    def __str__(self) -> str:
        return f"ImageResizer(method={self.method.value})"
