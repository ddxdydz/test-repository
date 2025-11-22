from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, Tuple

import numpy as np


class ResizeMethod(Enum):
    """Перечисление методов изменения размера"""
    NEAREST = "nearest"
    BILINEAR = "bilinear"
    BICUBIC = "bicubic"
    LANCZOS = "lanczos"
    AREA = "area"
    LINEAR_EXACT = "exlinear"
    NEAREST_EXACT = "nearest_ exact"

    @classmethod
    def get_by_index(cls, index: int):
        """Получить метод по индексу"""
        members = list(cls)
        if 0 <= index < len(members):
            return members[index]
        raise IndexError(f"Index {index} out of range")

    def get_index(self) -> int:
        """Получить индекс текущего метода"""
        return list(self.__class__).index(self)


class ImageResizer(ABC):
    """
    Абстрактный класс для изменения размера изображений
    с поддержкой прямого и обратного преобразования
    """

    def __init__(self, scale: float, method: ResizeMethod | int, original_size: Optional[Tuple[int, int]]):
        self.name = self.__class__.__name__
        self.scale = self._get_validated_scale(scale)
        self.method = self._get_validated_method(method)
        self.original_size = None
        self.target_size = None
        self.set_original_size(original_size)

    @staticmethod
    def calculate_target_size(original_size: Tuple[int, int], scale: float) -> Tuple[int, int]:
        """Вычислить целевой размер на основе исходного размера и масштаба"""
        return max(1, round(original_size[0] * scale)), max(1, round(original_size[1] * scale))

    @staticmethod
    def _get_validated_scale(scale: float) -> float:
        if scale <= 0:
            raise ValueError(f"Error in ImageResizer: Scale must be positive")
        return scale

    @staticmethod
    def _get_validated_size(size: Tuple[int, int]) -> Tuple[int, int]:
        """Получить валидированный размер изображения"""
        if not isinstance(size, tuple) or len(size) != 2:
            raise ValueError("Error in ImageResizer: original_size must be a tuple of two integers")
        if size[0] <= 0 or size[1] <= 0:
            raise ValueError("Error in ImageResizer: Image dimensions must be positive")
        return size

    @staticmethod
    def _get_validated_method(method: ResizeMethod | int) -> ResizeMethod:
        """Валидировать и конвертировать метод в ResizeMethod"""
        if isinstance(method, ResizeMethod):
            return method
        elif isinstance(method, int):
            return ResizeMethod.get_by_index(method)
        else:
            raise TypeError(f"Error in ImageResizer: Method must be ResizeMethod or int, got {type(method)}")

    def set_original_size(self, original_size: Tuple[int, int] | None) -> None:
        """Установить новый исходный размер и пересчитать целевой размер"""
        if original_size is None:
            self.original_size = None
            self.target_size = None
        else:
            self.original_size = self._get_validated_size(original_size)
            self.target_size = self.calculate_target_size(original_size, self.scale)

    def set_scale(self, scale: float) -> None:
        """Установить новый коэффициент масштабирования"""
        self.scale = self._get_validated_scale(scale)
        if self.original_size is not None:
            self.target_size = self.calculate_target_size(self.original_size, self.scale)

    def set_method(self, method: ResizeMethod | int) -> ResizeMethod:
        """Установить новый метод масштабирования"""
        self.method = self._get_validated_method(method)
        return self.method

    def get_parameters(self) -> Tuple[Optional[Tuple[int, int]], float, int]:
        """Получить текущие параметры масштабирования"""
        return *self.original_size, self.scale, self.method.get_index()

    @abstractmethod
    def _basic_resize(self, image: np.array, target_size: Tuple[int, int]) -> np.array:
        """Абстрактный метод для базового изменения размера"""
        ...

    def resize(self, image: np.array) -> np.array:
        """Изменить размер изображения до целевого размера"""
        image_size = (image.shape[1], image.shape[0])
        if self.scale + 0.01 > 1:
            return image
        if self.original_size is None:
            return self._basic_resize(image, self.calculate_target_size(image_size, self.scale))
        if image_size != self.original_size:
            raise ValueError(f"Image size {image.size} doesn't match expected original size {self.original_size}")
        return self._basic_resize(image, self.target_size)

    def desize(self, image: np.array) -> np.array:
        """Вернуть изображение к исходному размеру"""
        image_size = (image.shape[1], image.shape[0])
        if self.scale + 0.01 > 1:
            return image
        if self.original_size is None:
            return self._basic_resize(image, self.calculate_target_size(image_size, 1 / self.scale))
        if image_size != self.target_size:
            raise ValueError(f"Image size {image.size} doesn't match expected target size {self.target_size}")
        return self._basic_resize(image, self.original_size)

    @staticmethod
    def get_compress_coefficient(scale: float) -> float:
        """Рассчитать процент потери 'веса' при масштабировании"""
        if scale <= 0:
            raise ValueError("Scale must be positive")
        return scale ** 2

    @staticmethod
    def print_compress_table() -> None:
        """Напечатать таблицу потерь для разных масштабов"""
        scales_info = []
        for scale_100 in range(99, 0, -1):
            scale = scale_100 / 100
            scales_info.append(f"{scale:.2f} = {ImageResizer.get_compress_coefficient(scale) * 100:.2f} %")
        print("\n".join(scales_info))

    def __str__(self) -> str:
        """Строковое представление объекта"""
        loss = self.get_compress_coefficient(self.scale) if self.scale > 0 else "N/A"
        return f"{self.name}(scale={self.scale}, method={self.method.name}): {loss}"

    def __repr__(self) -> str:
        """Репрезентативное строковое представление"""
        return (f"{self.__class__.__name__}(original_size={self.original_size}, "
                f"scale={self.scale}, method={self.method})")


if __name__ == "__main__":
    ImageResizer.print_compress_table()
