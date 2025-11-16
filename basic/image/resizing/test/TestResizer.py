from pathlib import Path
from time import time

from PIL import Image

from basic.image.resizing.ABC_ImageResizer import ImageResizer, ResizeMethod


class TestResizer:
    BASE_DIR = Path(__file__).parent.parent.parent
    TEMP_PATH = BASE_DIR / "resizing" / "test" / "temp_data"
    METHODS = [ResizeMethod.NEAREST, ResizeMethod.AREA, ResizeMethod.BILINEAR,
               ResizeMethod.BICUBIC, ResizeMethod.LANCZOS]
    SCALE = 0.6

    def __init__(self, resizer: ImageResizer, img_path: Path, iteration_count: int = 20):
        self.img_type = img_path.name[img_path.name.rfind("."):]
        self.iteration_count = iteration_count
        self.original_image = Image.open(img_path)
        self.original_image.save(f"{TestResizer.TEMP_PATH}\\0{self.img_type}")
        self.resizer = resizer
        self.resizer.reset_original_size(self.original_image.size)

    def test_method(self, method: ResizeMethod, enable_print=True):
        self.resizer.reset_method(method)
        total_resize_time = 0
        total_desize_time = 0
        desized_img = None
        for _ in range(self.iteration_count):
            start = time()
            resized_img = self.resizer.resize(self.original_image)
            total_resize_time += time() - start
            start = time()
            desized_img = self.resizer.desize(resized_img)
            total_desize_time += time() - start
        resize_time = round(total_resize_time / self.iteration_count, 6)
        desize_time = round(total_desize_time / self.iteration_count, 6)

        if enable_print:
            print(f"{method.name.ljust(10)}\t\tresize_time={resize_time} c\t\tdesize_time={desize_time} c")

        return desized_img

    def test(self):
        print(self.resizer)
        for i in range(len(TestResizer.METHODS)):
            method = TestResizer.METHODS[i]
            self.test_method(method).save(f"{TestResizer.TEMP_PATH}\\{i + 1} {method.name}{self.img_type}")
