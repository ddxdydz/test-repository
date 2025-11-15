from enum import Enum
from PIL import Image

from basic.image.resizing.support.ResizeMethod import ResizeMethod


class ImageScaler:
    """Базовый класс для изменения размера изображения"""

    def __init__(self, scale: float = 0.7, method: ResizeMethod | int = ResizeMethod.BILINEAR):
        self.name = self.__class__.__name__
        self.method = method
        self.scale = scale
        self.reversed_scale = 1 / scale

    def set_scale(self, scale: int):
        self.scale = scale
        self.reversed_scale = 1 / scale

    def _resize_basic(self, image: Image.Image, target_size: tuple[int, int]) -> Image.Image:
        if image.mode != 'RGB':
            image = image.convert('RGB')
        return image.resize(target_size, self._get_pil_resample())

    def get_target_size(self, size: tuple[int, int]) -> tuple[int, int]:
        return round(size[0] * self.scale), round(size[1] * self.scale)

    def get_original_size(self, size: tuple[int, int]) -> tuple[int, int]:
        return round(size[0] * self.reversed_scale / 10) * 10, round(size[1] * self.reversed_scale / 10) * 10

    def resize(self, image: Image.Image) -> Image.Image:
        return self._resize_basic(image, self.get_target_size(image.size))

    def desize(self, image: Image.Image) -> Image.Image:
        return self._resize_basic(image, self.get_original_size(image.size))

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

    def get_weight_loss_percent(self, scale: float = None) -> str:
        if scale is None:
            scale = self.scale
        return f"{round(scale ** 2, 5) * 100}%"

    def print_weight_loss_percents(self):
        for scale_10 in range(9, 0, -1):
            scale = scale_10 / 10
            print(f"{scale}={self.get_weight_loss_percent(scale)}", end="\t")
        print()

    def __str__(self) -> str:
        return f"{self.name}(scale={self.scale}, method={self.method.value})"


if __name__ == "__main__":
    scaler = ImageScaler(0.63)
    scaler.print_weight_loss_percents()
    print(scaler, scaler.get_original_size(scaler.get_target_size((800, 740))))
