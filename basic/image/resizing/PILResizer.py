from PIL import Image

from basic.image.resizing.support.ImageResizer import ImageResizer
from basic.image.resizing.support.ResizeMethod import ResizeMethod
from basic.image.resizing.support.ResizeTask import ResizeTask


class PILResizer(ImageResizer):
    """Реализация изменения размера с использованием PIL"""
    def __init__(self, resize_task: ResizeTask, method: ResizeMethod = ResizeMethod.BILINEAR):
        super().__init__(method)
        self.resize_task = resize_task
        self.desize_task = None if resize_task.scale is None else ResizeTask(1 / resize_task.scale)

    def resize(self, image: Image.Image) -> Image.Image:
        return self.resize_basic(image, self.resize_task.calculate_size(image.size))

    def desize(self, image: Image.Image) -> Image.Image:
        if self.desize_task is None:
            return image
        return self.resize_basic(image, self.desize_task.calculate_size(image.size))
