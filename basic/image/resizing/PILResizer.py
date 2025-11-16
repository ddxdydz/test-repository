from typing import Tuple

import numpy as np
from PIL import Image

from basic.image.resizing.ABC_ImageResizer import ImageResizer, ResizeMethod


class PILResizer(ImageResizer):
    """Базовый класс для изменения размера изображения"""
    _PIL_MAPPING = {
        ResizeMethod.NEAREST: Image.NEAREST,
        ResizeMethod.BILINEAR: Image.BILINEAR,
        ResizeMethod.BICUBIC: Image.BICUBIC,
        ResizeMethod.LANCZOS: Image.LANCZOS,
        ResizeMethod.AREA: Image.BOX
    }

    def __init__(self, scale: float = 0.6, method: ResizeMethod | int = ResizeMethod.LANCZOS,
                 original_size: tuple[int, int] | None = None):
        super().__init__(scale, method, original_size)

    def _basic_resize(self, image: np.array, target_size: Tuple[int, int]) -> np.array:
        image = Image.fromarray(image)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        return np.array(image.resize(target_size, PILResizer._PIL_MAPPING[self.method]), dtype=np.uint8)


if __name__ == "__main__":
    from pathlib import Path
    from basic.image.resizing.test.TestResizer import TestResizer
    image_path = Path(__file__).parent.parent / "data" / "v10.png"
    test_pil = TestResizer(PILResizer(scale=0.6), image_path, 100)
    test_pil.DATA_PATH = image_path
    test_pil.test()
