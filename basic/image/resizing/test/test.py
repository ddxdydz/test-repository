from pathlib import Path
from time import time

from PIL import Image

from basic.image.resizing.ImageScaler import ImageScaler, ResizeMethod

BASE_DIR = Path(__file__).parent.parent.parent
TEMP_PATH = BASE_DIR / "resizing" / "test" / "temp"
DATA_PATH = BASE_DIR / "data" / "v10.png"
IMG_TYPE = DATA_PATH.name[DATA_PATH.name.rfind("."):]
ITERATION_COUNT = 20
SCALE = 0.7


def test(resizer, enable_print=True, i_count=ITERATION_COUNT):
    input_image = Image.open(DATA_PATH)

    total_resize_time = 0
    total_desize_time = 0
    desized_img = None
    for _ in range(i_count):
        start = time()
        resized_img = resizer.resize(input_image)
        total_resize_time += time() - start
        start = time()
        desized_img = resizer.desize(resized_img)
        total_desize_time += time() - start
    resize_time = round(total_resize_time / i_count, 6)
    desize_time = round(total_desize_time / i_count, 6)

    if enable_print:
        print(f"{resizer.method.name.ljust(10)}\t\tresize_time={resize_time} c\t\tdesize_time={desize_time} c")

    return desized_img


def test_resizer_methods(resizer):
    print(resizer.name)
    methods = [ResizeMethod.NEAREST, ResizeMethod.AREA, ResizeMethod.BILINEAR,
               ResizeMethod.BICUBIC, ResizeMethod.LANCZOS]
    for i in range(len(methods)):
        resizer.method = methods[i]
        test(resizer).save(f"{TEMP_PATH}\\{i + 1} {resizer.method.name}{IMG_TYPE}")


if __name__ == "__main__":
    original_image = Image.open(DATA_PATH)
    scale = 0.7

    scaler = ImageScaler(scale)
    test_resizer_methods(scaler)

    original_image.save(f"{TEMP_PATH}\\0{IMG_TYPE}")
    print(scaler.get_weight_loss_percent())
