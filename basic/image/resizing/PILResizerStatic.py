from typing import Optional, Tuple

from PIL import Image

from basic.image.resizing.support.ImageResizer import ImageResizer
from basic.image.resizing.support.ResizeMethod import ResizeMethod
from basic.image.resizing.support.ResizeTask import ResizeTask


class StaticPILResizer(ImageResizer):
    def __init__(self,
                 original_size: Optional[Tuple[int, int]],
                 scale: Optional[float] = None,
                 size: Optional[Tuple[int, int]] = None,
                 max_size: Optional[Tuple[int, int]] = None,
                 width: Optional[int] = None,
                 height: Optional[int] = None,
                 method: ResizeMethod = ResizeMethod.BILINEAR,
                 ):
        super().__init__(method)
        self.task = ResizeTask(scale, size, max_size, width, height)
        self.original_size = original_size
        self.target_size = self.task.calculate_size(original_size)

    def resize(self, image: Image.Image) -> Image.Image:
        return self.resize_basic(image, self.target_size)

    def desize(self, image: Image.Image) -> Image.Image:
        return self.resize_basic(image, self.original_size)
