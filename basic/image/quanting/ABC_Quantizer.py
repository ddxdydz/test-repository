from abc import ABC, abstractmethod

import cv2
import numpy as np


class Quantizer(ABC):
    """Абстрактный базовый класс для квантователей"""

    def __init__(self, colors, use_cv_optimizations=True):
        if not (1 < colors < 257):
            raise ValueError("Number of colors must be between 1 and 256")
        self.COLORS = colors
        self.bits_per_color = (self.COLORS - 1).bit_length()

        if use_cv_optimizations:
            cv2.setNumThreads(0)  # Использовать все ядра
            cv2.useOptimized()  # Включить SIMD оптимизации

        self._quant_lut = np.array([self._value_to_quant(i) for i in range(256)], dtype=np.uint8)
        self._dequant_lut = np.array(
            [self._quant_to_value(min(i, self.COLORS - 1)) for i in range(256)], dtype=np.uint8)

    def _value_to_quant(self, value: int) -> int:
        """Convert pixel value (0-255) to quantization level"""
        if self.COLORS == 1:
            return 0
        return min(value // (256 // self.COLORS), self.COLORS - 1)

    def _quant_to_value(self, quant: int) -> int:
        """Convert quantization level back to pixel value (0-255)"""
        if not 0 <= quant < self.COLORS:
            raise ValueError(f"Quant level must be between 0 and {self.COLORS - 1}")

        if self.COLORS == 1:
            return 255

        return int((quant * 255) / (self.COLORS - 1))

    @abstractmethod
    def quantize(self, image: np.ndarray) -> np.ndarray:
        pass

    @abstractmethod
    def dequantize(self, image: np.ndarray) -> np.ndarray:
        pass

    @abstractmethod
    def pack_quantized(self, quantized_image: np.ndarray) -> bytes:
        pass

    @abstractmethod
    def unpack_quantized(self, data: bytes, image_width: int, image_height: int) -> np.ndarray:
        pass

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(colors={self.COLORS}, bits_per_color={self.bits_per_color})"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(colors={self.COLORS})"
