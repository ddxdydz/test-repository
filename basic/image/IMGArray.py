from pathlib import Path
from typing import Optional, Union

import numpy as np
from PIL import Image


class IMGArray:
    """
    Класс для работы с изображениями в различных представлениях.
    Поддерживает создание из PIL.Image, пути к файлу или numpy массива.
    Автоматически конвертирует изображение в RGB при необходимости.
    """

    def __init__(self,
                 pil_image: Optional[Image.Image] = None,
                 image_path: Optional[Path] = None,
                 numpy_array: Optional[np.ndarray] = None):
        if numpy_array is not None:
            if numpy_array.dtype != np.uint8:
                raise ValueError(f"Array must have dtype uint8, got {numpy_array.dtype}")
            self.array = numpy_array
        elif pil_image is not None:
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            self.array = np.array(pil_image, dtype=np.uint8)
        elif image_path is not None:
            if not image_path.exists():
                raise FileNotFoundError(f"Файл не найден: {image_path}")
            try:
                pil_image = Image.open(image_path)
                if pil_image.mode != 'RGB':
                    pil_image = pil_image.convert('RGB')
            except Exception as e:
                raise ValueError(f"Ошибка загрузки изображения {image_path}: {e}")
            self.array = np.array(pil_image, dtype=np.uint8)
        else:
            raise ValueError("Не указан источник изображения в IMGArray")

    @property
    def image_size(self) -> tuple[int, int]:
        """Возвращает размер изображения (ширина, высота)."""
        return self.array.shape[1], self.array.shape[0]

    @property
    def width(self) -> int:
        """Ширина изображения в пикселях."""
        return self.array.shape[1]

    @property
    def height(self) -> int:
        """Высота изображения в пикселях."""
        return self.array.shape[0]

    @property
    def channels(self) -> int:
        """Количество каналов в изображении."""
        return self.array.shape[2] if len(self.array.shape) == 3 else 1

    @property
    def shape(self) -> tuple:
        """Форма numpy массива (height, width, channels)."""
        return self.array.shape

    def get_pil_image(self) -> Image.Image:
        """Возвращает изображение в формате PIL.Image."""
        return Image.fromarray(self.array)  # Возвращаем копию для безопасности

    def show(self):
        self.get_pil_image().show()

    def save(self, file_path: Union[Path], **kwargs) -> None:
        """
        Сохраняет изображение в файл.

        Args:
            file_path: Путь для сохранения
            **kwargs: Дополнительные параметры для PIL.Image.save()
        """
        file_path = Path(file_path)
        self.get_pil_image().save(file_path, **kwargs)

    def __repr__(self) -> str:
        return f"IMGArray(size={self.width}x{self.height}, channels={self.channels})"
