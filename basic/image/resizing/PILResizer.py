from typing import Tuple

import numpy as np
from PIL import Image

from basic.image.resizing.ABC_ImageResizer import ImageResizer, ResizeMethod


class PILResizer(ImageResizer):
    """Базовый класс для изменения размера изображения"""
    _PIL_MAPPING = {
        "NEAREST": Image.NEAREST,
        "BILINEAR": Image.BILINEAR,
        "BICUBIC": Image.BICUBIC,
        "LANCZOS": Image.LANCZOS,
        "AREA": Image.BOX
    }

    def __init__(self, scale: float = 0.6, method: ResizeMethod | int = ResizeMethod.LANCZOS,
                 original_size: tuple[int, int] | None = None):
        super().__init__(scale, method, original_size)
        self.pil_resample = PILResizer._PIL_MAPPING[self.method.name]

    def _basic_resize(self, image: np.array, target_size: Tuple[int, int]) -> np.array:
        image = Image.fromarray(image)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        return np.array(image.resize(target_size, self.pil_resample), dtype=np.uint8)


if __name__ == "__main__":
    # input_image = np.array(Image.open(image_path), dtype=np.uint8)
    # from time import time
    # scaler = PILResizer(0.6, ResizeMethod.LANCZOS, input_image.size)
    # start_time = time()
    # resized_img = scaler.resize(input_image)
    # resize_time = time() - start_time
    # print("scaler.resize", f"{resize_time}s", sep="\t")
    # start_time = time()
    # _ = scaler.resize(input_image)
    # resize_time = time() - start_time
    # print("scaler.resize", f"{resize_time}s", sep="\t")
    # start_time = time()
    # desized_img = scaler.desize(resized_img)
    # desize_time = time() - start_time
    # print("scaler.desize", f"{desize_time}s", sep="\t")
    # start_time = time()
    # _ = scaler.desize(resized_img)
    # desize_time = time() - start_time
    # print("scaler.desize", f"{desize_time}s", sep="\t")
    # desized_img.show()

    from pathlib import Path
    from basic.image.resizing.test.TestResizer import TestResizer
    image_path = Path(__file__).parent.parent / "data" / "v10.png"
    test_pil = TestResizer(PILResizer(scale=0.6), image_path, 100)
    test_pil.DATA_PATH = image_path
    test_pil.test()

"""
CVResizer(scale=0.6, method=LANCZOS): 36.00%
NEAREST   		resize_time=0.00613 c		desize_time=0.00445 c
AREA      		resize_time=0.004296 c		desize_time=0.004356 c
BILINEAR  		resize_time=0.00419 c		desize_time=0.004272 c
BICUBIC   		resize_time=0.004057 c		desize_time=0.004136 c
LANCZOS   		resize_time=0.004327 c		desize_time=0.004309 c
"""
