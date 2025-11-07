from abc import ABC, abstractmethod

from PIL import Image


class BaseQuantizer(ABC):
    """Абстрактный базовый класс для квантователей"""

    def __init__(self, colors=3):
        if not (1 < colors < 257):
            raise ValueError("Number of colors must be between 1 and 256")
        self.COLORS = colors

    def value_to_quant(self, value: int) -> int:
        """Convert pixel value (0-255) to quantization level"""
        if self.COLORS == 1:
            return 0
        return min(value // (256 // self.COLORS), self.COLORS - 1)

    def quant_to_value(self, quant: int) -> int:
        """Convert quantization level back to pixel value (0-255)"""
        if not 0 <= quant < self.COLORS:
            raise ValueError(f"Quant level must be between 0 and {self.COLORS - 1}")

        if self.COLORS == 1:
            return 255

        return int((quant * 255) / (self.COLORS - 1))

    @abstractmethod
    def quantize(self, img: Image) -> [int]:
        """Абстрактный метод для квантования изображения"""
        pass

    @abstractmethod
    def dequantize(self, quantize_data: bytes, width: int, height: int) -> [int]:
        """Абстрактный метод для восстановления изображения"""
        pass
