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

    def _basic_resize(self, image: Image.Image, target_size: tuple[int, int]) -> Image.Image:
        if image.mode != 'RGB':
            image = image.convert('RGB')
        return image.resize(target_size, self.pil_resample)


if __name__ == "__main__":
    from pathlib import Path
    image_path = Path(__file__).parent.parent / "data" / "v10.png"
    input_image = Image.open(image_path)
    from time import time

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

    from basic.image.resizing.test.TestResizer import TestResizer
    test_pil = TestResizer(PILResizer(scale=0.6), image_path, 20)
    test_pil.DATA_PATH = image_path
    test_pil.ITERATION_COUNT = 1
    test_pil.test()
