import os
from time import time

from PIL import Image

from ImageCompressor import ImageCompressor


def test_speed(count=1, cpr_alg=0, qua_met=0, colors=4, image_path=None):
    if image_path is None:
        return

    compressor = ImageCompressor(cpr_alg, qua_met, colors)
    input_image = Image.open(image_path)

    compress_data = 0
    total_time = 0
    for _ in range(count):
        time_start11 = time()
        compress_data, _ = compressor.compress(input_image)
        total_time += time() - time_start11
    average = total_time / count

    print(
        (cpr_alg, qua_met, colors),
        image_path[image_path.rfind('\\') + 1:],
        input_image.size,
        f"{len(compress_data) // 1024} KB",
        f"{average} с.",
        sep="\t"
    )


def test_speed_image():
    pass


# test_speed(4, 0, 0, 4, r"C:\Users\UserLog.ru\PycharmProjects\regular\basic\image\data\v4.png")
# test_speed(4, 0, 0, 2, r"C:\Users\UserLog.ru\PycharmProjects\regular\basic\image\data\v4.png")

test_speed(4, 0, 0, 7, r"C:\Users\UserLog.ru\PycharmProjects\regular\basic\image\data\v9.png")
test_speed(4, 0, 0, 6, r"C:\Users\UserLog.ru\PycharmProjects\regular\basic\image\data\v9.png")
test_speed(4, 0, 0, 5, r"C:\Users\UserLog.ru\PycharmProjects\regular\basic\image\data\v9.png")
test_speed(4, 0, 0, 4, r"C:\Users\UserLog.ru\PycharmProjects\regular\basic\image\data\v9.png")
test_speed(4, 0, 0, 3, r"C:\Users\UserLog.ru\PycharmProjects\regular\basic\image\data\v9.png")
test_speed(4, 0, 0, 2, r"C:\Users\UserLog.ru\PycharmProjects\regular\basic\image\data\v9.png")

test_speed(4, 1, 0, 7, r"C:\Users\UserLog.ru\PycharmProjects\regular\basic\image\data\v9.png")
test_speed(4, 1, 0, 6, r"C:\Users\UserLog.ru\PycharmProjects\regular\basic\image\data\v9.png")
test_speed(4, 1, 0, 5, r"C:\Users\UserLog.ru\PycharmProjects\regular\basic\image\data\v9.png")
test_speed(4, 1, 0, 4, r"C:\Users\UserLog.ru\PycharmProjects\regular\basic\image\data\v9.png")
test_speed(4, 1, 0, 3, r"C:\Users\UserLog.ru\PycharmProjects\regular\basic\image\data\v9.png")
test_speed(4, 1, 0, 2, r"C:\Users\UserLog.ru\PycharmProjects\regular\basic\image\data\v9.png")

test_speed(4, 2, 0, 7, r"C:\Users\UserLog.ru\PycharmProjects\regular\basic\image\data\v9.png")
test_speed(4, 2, 0, 6, r"C:\Users\UserLog.ru\PycharmProjects\regular\basic\image\data\v9.png")
test_speed(4, 2, 0, 5, r"C:\Users\UserLog.ru\PycharmProjects\regular\basic\image\data\v9.png")
test_speed(4, 2, 0, 4, r"C:\Users\UserLog.ru\PycharmProjects\regular\basic\image\data\v9.png")
test_speed(4, 2, 0, 3, r"C:\Users\UserLog.ru\PycharmProjects\regular\basic\image\data\v9.png")
test_speed(4, 2, 0, 2, r"C:\Users\UserLog.ru\PycharmProjects\regular\basic\image\data\v9.png")

test_speed(4, 3, 0, 7, r"C:\Users\UserLog.ru\PycharmProjects\regular\basic\image\data\v9.png")
test_speed(4, 3, 0, 6, r"C:\Users\UserLog.ru\PycharmProjects\regular\basic\image\data\v9.png")
test_speed(4, 3, 0, 5, r"C:\Users\UserLog.ru\PycharmProjects\regular\basic\image\data\v9.png")
test_speed(4, 3, 0, 4, r"C:\Users\UserLog.ru\PycharmProjects\regular\basic\image\data\v9.png")
test_speed(4, 3, 0, 3, r"C:\Users\UserLog.ru\PycharmProjects\regular\basic\image\data\v9.png")
test_speed(4, 3, 0, 2, r"C:\Users\UserLog.ru\PycharmProjects\regular\basic\image\data\v9.png")


# test_speed(4, 0, 0, 4, r"C:\Users\UserLog.ru\PycharmProjects\regular\basic\image\data\v7.png")
# test_speed(4, 0, 0, 2, r"C:\Users\UserLog.ru\PycharmProjects\regular\basic\image\data\v7.png")
#
# test_speed(4, 0, 0, 4, r"C:\Users\UserLog.ru\PycharmProjects\regular\basic\image\data\v10.png")
# test_speed(4, 0, 0, 2, r"C:\Users\UserLog.ru\PycharmProjects\regular\basic\image\data\v10.png")
