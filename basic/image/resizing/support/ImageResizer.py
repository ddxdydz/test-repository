from PIL import Image
from abc import ABC, abstractmethod
from basic.image.resizing.support.ResizeMethod import ResizeMethod


class ImageResizer(ABC):
    """Базовый класс для изменения размера изображения"""

    def __init__(self, method: ResizeMethod = ResizeMethod.BILINEAR):
        self.method = method
        self.name = self.__class__.__name__

    def resize_basic(self, image: Image.Image, target_size: tuple[int, int]) -> Image.Image:
        # Конвертируем в RGB если нужно (для корректной работы с JPEG)
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Изменяем размер
        resized_img = image.resize(target_size, self._get_pil_resample())

        return resized_img

    @abstractmethod
    def resize(self, image: Image.Image) -> Image.Image:
        ...

    @abstractmethod
    def desize(self, image: Image.Image) -> Image.Image:
        ...

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
        return f"{self.name}(method={self.method.value})"
