from typing import Tuple
from basic.image.resizing.ABC_ImageResizer import ImageResizer

import numpy as np


class GrayscaleDifferenceHandler:
    def __init__(self, max_value: int, scale_percent: int, shape: Tuple[int, int]):
        self.name = self.__class__.__name__

        if not (0 < max_value < 256):
            raise ValueError(f"{self.name}: Number of max_value must be between 1 and 255, got {max_value}")

        if scale_percent < 1 or scale_percent > 100:
            raise ValueError(f"{self.name}: Scale percent must be between 1 and 100, got {scale_percent}")

        if shape[0] <= 0 or shape[1] <= 0:
            raise ValueError(f"{self.name}: Image dimensions must be positive, got {shape}")

        self.max_value = max_value
        self.scale_percent = scale_percent
        self.reference_shape = ImageResizer.calculate_target_size(shape, self.scale_percent / 100)
        self._reference_frame = np.zeros(self.reference_shape, dtype=np.uint8)

    def _validate_frame_shape(self, frame: np.ndarray) -> None:
        """Проверяет соответствие формы кадра ожидаемой."""
        if frame.shape != self.reference_shape:
            raise ValueError(
                f"{self.name}: Expected frame shape {self.reference_shape}, "
                f"got {frame.shape}"
            )

    def compute_difference(self, current_frame: np.ndarray) -> np.ndarray:
        """
        Вычисляет разностный кадр между текущим и reference кадром.

        Args:
            current_frame: Текущий кадр для сравнения

        Returns:
            Разностный кадр в диапазоне [0, max_value-1]
        """
        self._validate_frame_shape(current_frame)

        # Оптимизированное вычисление разности по модулю
        difference = np.subtract(
            self._reference_frame.astype(np.int16),  # Предотвращаем переполнение
            current_frame.astype(np.int16),
            dtype=np.int16
        )  # D = R - C
        difference = np.mod(difference, self.max_value, dtype=np.int16)

        return difference.astype(np.uint8)

    def apply_difference(self, difference_frame: np.ndarray) -> np.ndarray:
        """
        Применяет разностный кадр к reference frame и возвращает результат.

        Args:
            difference_frame: Разностный кадр для применения

        Returns:
            Новый реконструированный кадр
        """
        self._validate_frame_shape(difference_frame)

        # Вычисляем новый кадр с применением разности
        new_frame = np.subtract(
            self._reference_frame.astype(np.int16),
            difference_frame.astype(np.int16),
            dtype=np.int16
        )  # R - D = R - (R - C) = C
        new_frame = np.mod(new_frame, self.max_value, dtype=np.int16)
        new_frame = new_frame.astype(np.uint8)

        self._reference_frame = new_frame

        return new_frame

    def update_reference(self, new_frame: np.ndarray) -> None:
        """
        Обновляет reference frame новым кадром.

        Args:
            new_frame: Новый reference frame
        """
        self._validate_frame_shape(new_frame)
        self._reference_frame = new_frame.astype(np.uint8)

    @property
    def reference_frame(self) -> np.ndarray:
        """Возвращает копию текущего reference frame."""
        return self._reference_frame.copy()

    @property
    def frame_size(self) -> Tuple[int, int]:
        """Возвращает размер кадра (height, width)."""
        return self.reference_shape


if __name__ == "__main__":
    from pathlib import Path
    from PIL import Image
    from time import time
    from basic.image.compression.base_compressors import BZ2Compressor
    from basic.image.packing.NoTampingPacker import NoTampingPacker
    from basic.image.quanting.GrayQuantizer import GrayQuantizer
    from basic.image.resizing.CVResizerIntScale import CVResizerIntScale

    diff_handler = GrayscaleDifferenceHandler(3, 60, (719, 1279))

    for image_name in ["ch1.jpg", "ch2.jpg", "ch3.jpg", "ch3.jpg"]:
        img_path = Path(__file__).parent.parent / "data" / image_name

        image = Image.open(img_path)
        img_array = np.asarray(image, dtype=np.uint8)
        if len(img_array.shape) == 3 and img_array.shape[2] == 4:
            img_array = img_array[:, :, :3]
        print(f"##### {image_name} #####")
        print(img_array.shape)

        resizer = CVResizerIntScale(scale_percent=60, original_size=(img_array.shape[1], img_array.shape[0]))
        quantizer = GrayQuantizer(3)
        packer = NoTampingPacker(quantizer.bits_per_color)
        compressor = BZ2Compressor()

        data = resizer.resize(img_array)

        quantized = quantizer.quantize(data)
        print("quantized size:", len(compressor.compress(packer.pack_array(quantized))), "B")
        _s_time = time()
        diffed = diff_handler.compute_difference(quantized)
        print("diffed", time() - _s_time)
        print("diffed size:", len(compressor.compress(packer.pack_array(diffed))), "B")

        data = compressor.decompress(compressor.compress(packer.pack_array(diffed)))
        data = packer.unpack_array(data)

        _s_time = time()
        # Image.fromarray(quantizer.dequantize(diff_handler._reference_frame)).show()
        data = diff_handler.apply_difference(data)
        # Image.fromarray(quantizer.dequantize(diff_handler._reference_frame)).show()
        print("diffed", time() - _s_time)

        data = quantizer.dequantize(data)
        data = resizer.desize(data)

        print(data.shape)
        Image.fromarray(data).show()
        input()



"""
without
10242 B
8889 B
8836 B

diffed 0.005341291427612305
10312 B
diffed 0.0053141117095947266
diffed 0.004683256149291992
3598 B
diffed 0.0042874813079833984
diffed 0.00432586669921875
77 B
diffed 0.0044324398040771484
"""
