from time import time

from PIL import Image

from basic.image.resizing.ImageScaler import ImageScaler
from basic.image.resizing.PILResizer import PILResizer
from basic.image.resizing.support.ImageResizer import ImageResizer
from basic.image.resizing.support.ResizeMethod import ResizeMethod
from basic.image.resizing.PILResizerStatic import StaticPILResizer
from basic.image.resizing.support.ResizeTask import ResizeTask

TEMP_PATH = r"C:\Users\UserLog.ru\PycharmProjects\regular\basic\image\resizing\test\temp"
PATH = r"C:\Users\UserLog.ru\PycharmProjects\regular\basic\image\data\v10.png"
IMG_TYPE = PATH[PATH.rfind("."):]
ITERATION_COUNT = 20
SCALE = 0.7


def test(resizer: ImageResizer, enable_save=True, enable_print=True, i_count=ITERATION_COUNT):
    input_image = Image.open(PATH)

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

    if enable_save and desized_img:
        desized_img.save(f"{TEMP_PATH}/1 {resizer.method.name}{IMG_TYPE}")

    if enable_print:
        print(f"{resizer.method.name.ljust(10)}\t\tresize_time={resize_time} c\t\tdesize_time={desize_time} c")

    return resizer.name, resize_time, desize_time


def test_resizer_methods(resizer: ImageResizer):
    print(resizer.name)
    methods = [ResizeMethod.NEAREST, ResizeMethod.AREA, ResizeMethod.BILINEAR,
               ResizeMethod.BICUBIC, ResizeMethod.LANCZOS]
    for method in methods:
        resizer.method = method
        test(resizer)


if __name__ == "__main__":
    scale_and_coef = [(i / 10, round((1 / (i / 10)) ** 2, 2)) for i in range(1, 10)]
    print(scale_and_coef)

    original_image = Image.open(PATH)
    scale = 0.7

    resizer = StaticPILResizer(original_image.size, scale=scale)
    test_resizer_methods(resizer)
    test_resizer_methods(PILResizer(ResizeTask(scale=scale)))
    test_resizer_methods(ImageScaler(scale))

    original_image.save(f"{TEMP_PATH}/0{IMG_TYPE}")
    target_size = resizer.target_size
    im_size, im_count_px = original_image.size, original_image.width * original_image.height
    rim_size, rim_count_px = resizer.target_size, resizer.target_size[0] * resizer.target_size[1]
    print(im_size, im_count_px)
    print(rim_size, rim_count_px)
    print(f"{round((rim_count_px / im_count_px) * 100, 2)} %", round(im_count_px / rim_count_px, 2))
