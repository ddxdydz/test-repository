from pathlib import Path
from time import time
from math import inf
import numpy as np
from PIL import Image

from basic.image.__all_tools import *


def prepare(input_image_array: np.array, input_scale: int, input_colors: int) -> bytes:
    resizer = CVResizerIntScale(input_scale)
    quantizer = GrayQuantizer(input_colors)
    packer = CombPacker(quantizer.bits_per_color)
    # _start_time = time()
    resized = resizer.resize(input_image_array)
    quantized = quantizer.quantize(resized)
    packed = packer.pack_array(quantized)
    # print(f"####### {scale}, {colors}")
    # print("preparation time".ljust(20), f"{time() - _start_time:.6f}")
    return packed


def generate_test_rgb_image_array(height: int, width: int) -> np.ndarray:
    data = np.random.randint(0, 256, size=(height, width, 3), dtype=np.uint8)
    return data


def generate_test_rgb_black_image_array(height: int, width: int) -> np.ndarray:
    data = np.full((height, width, 3), 255, dtype=np.uint8)
    return data


def get_compress_time(input_compressor: Compressor, data: bytes) -> float:
    _start_time = time()
    input_compressor.compress(data)
    return time() - _start_time


def print_data_weight_comparison_table(
        image: Path | np.ndarray,
        range_scale: tuple = (40, 100, 10),
        range_color: tuple = (3, 37, 1),
        col_width: int = 6) -> None:
    if isinstance(image, Path):
        print("IMAGE PATH:", image)
        image = Image.open(image)
        image_array = np.array(image, dtype=np.uint8)  # долго работает ~ 0.02
    else:
        image_array = image
    print("IMAGE SHAPE AND SIZE:", image_array.shape, image_array.size)
    print("ROWS/COLS: SCALE_PERCENT/COLORS_COUNT_FOR_QUANTING")
    print("CELLS: WEIGHT in Bytes")
    print(f"{str().ljust(col_width)}{''.join([f"{c}".ljust(col_width) for c in range(*range_color)])}")
    for scale in range(*range_scale):
        print(str(scale).ljust(col_width), end="")
        for colors in range(*range_color):
            prepared = prepare(image_array, scale, colors)
            print(f"{len(prepared)}".ljust(col_width), end="")
        print()


def print_compressor_speed_table(
        compressor1: Compressor,
        image: Path | np.ndarray,
        range_scale: tuple = (40, 100, 10),
        range_color: tuple = (3, 37, 1),
        col_width: int = 6) -> None:
    print(f"COMPRESSOR: {compressor1.name}")
    if isinstance(image, Path):
        print("IMAGE PATH:", image)
        image = Image.open(image)
        image_array = np.array(image, dtype=np.uint8)  # долго работает ~ 0.02
    else:
        image_array = image
    print("IMAGE SHAPE AND SIZE:", image_array.shape, image_array.size)
    print(f"MIN DATA WEIGHT (scale={range_scale[0]}, colors={range_color[0]}): ",
          len(prepare(image_array, range_scale[0], range_color[0])), "B")
    print(f"MAX DATA WEIGHT (scale={range_scale[1] - 1}, colors={range_color[1] - 1}): ",
          len(prepare(image_array, range_scale[1] - 1, range_color[1] - 1)), "B")
    print("ROWS/COLS: SCALE_PERCENT/COLORS_COUNT_FOR_QUANTING")
    print("CELLS: compression speed in ms")
    print(f"{str().ljust(col_width)}{''.join([f"{c}".ljust(col_width) for c in range(*range_color)])}")
    for scale in range(*range_scale):
        print(str(scale).ljust(col_width), end="")
        for colors in range(*range_color):
            prepared = prepare(image_array, scale, colors)
            time1 = get_compress_time(compressor1, prepared)
            print(f"{int(time1 * 1000)}".ljust(col_width), end="")
        print()


def print_compressors_speed_comparison_table(
        compressor1: Compressor,
        compressor2: Compressor,
        image: Path | np.ndarray,
        range_scale: tuple = (40, 100, 10),
        range_color: tuple = (3, 37, 1),
        col_width: int = 6) -> None:

    print(f"COMPRESSOR1: {compressor1.name}, COMPRESSOR2: {compressor2.name}")

    if isinstance(image, Path):
        print("IMAGE PATH:", image)
        image = Image.open(image)
        image_array = np.array(image, dtype=np.uint8)  # долго работает ~ 0.02
    else:
        image_array = image
    print("IMAGE SHAPE AND SIZE:", image_array.shape, image_array.size)
    print(f"MIN DATA WEIGHT (scale={range_scale[0]}, colors={range_color[0]}): ",
          len(prepare(image_array, range_scale[0], range_color[0])), "B")
    print(f"MAX DATA WEIGHT (scale={range_scale[1] - 1}, colors={range_color[1] - 1}): ",
          len(prepare(image_array, range_scale[1] - 1, range_color[1] - 1)), "B")
    print("ROWS/COLS: SCALE_PERCENT/COLORS_COUNT_FOR_QUANTING")
    print("CELLS: ratio = compress_1_time / compress_2_time")
    print(f"{str().ljust(col_width)}{''.join([f"{c}".ljust(col_width) for c in range(*range_color)])}")
    for scale in range(*range_scale):
        print(str(scale).ljust(col_width), end="")
        for colors in range(*range_color):
            prepared = prepare(image_array, scale, colors)
            time1 = get_compress_time(compressor1, prepared)
            time2 = get_compress_time(compressor2, prepared)
            if time1 < 0.01 and time2 < 0.01:
                ratio = 1
            elif not time2 > 0:
                ratio = inf
            else:
                ratio = time1 / time2
            # print(f'{scale}-{colors}-{f"{ratio:.1f}".ljust(col_width)}({time1:.4f}/{time2:.4f})', end="")
            print(f"{ratio:.1f}".ljust(col_width), end="")
        print()


for img_name in ["a2.png", "a3.png", "a4.png", "a5.png", "a6.png", "a7.png", "a8.png", "a9.png", "a10.png",
                 "g1.png", "g2.png"]:  # на a10
    print_compressors_speed_comparison_table(
        TryCompressor(), BZ2Compressor(),
        Path(__file__).parent / "data" / img_name,
        (40, 100, 10), (3, 37, 1)
    )
    print_compressors_speed_comparison_table(
        TryCompressor(), ZlibCompressor(),
        Path(__file__).parent / "data" / img_name,
        (40, 100, 10), (3, 37, 1)
    )

# !!!
# print_compressors_speed_comparison_table(
#      MultiCompressor(), BZ2Compressor(),
#      Path(__file__).parent / "data" / "a7.png",
#      (40, 100, 10), (3, 37, 1)
# )
# print_data_weight_comparison_table(Path(__file__).parent / "data" / "a7.png", (40, 100, 10), (3, 37, 1))


# random_im = generate_test_rgb_image_array(1000, 1000)
# black_im = generate_test_rgb_image_array(1000, 1000)
# print_compressors_speed_comparison_table(
#     BZ2Compressor(), ZlibCompressor(), g,
#     (40, 101, 10), (3, 37, 1)
# )
# print_data_weight_comparison_table(g, (40, 101, 10), (3, 37, 1))
# print_compressor_speed_table(
#     BZ2Compressor(), random_im,
#     (40, 101, 10), (3, 37, 1)
# )
# print_compressor_speed_table(
#     BZ2Compressor(), black_im,
#     (40, 101, 10), (3, 37, 1)
# )
# print_compressor_speed_table(
#     ZlibCompressor(), random_im,
#     (40, 101, 10), (3, 37, 1)
# )
# print_compressor_speed_table(
#     ZlibCompressor(), black_im,
#     (40, 101, 10), (3, 37, 1)
# )

"""
COMPRESSOR1: MultiCompressor, COMPRESSOR2: BZ2Compressor
a7.png
IMAGE SHAPE AND SIZE: (489, 746, 4) 1459176
MIN DATA WEIGHT (scale=40, colors=3):  14607 B
MAX DATA WEIGHT (scale=99, colors=36):  286149 B
ROWS/COLS: SCALE_PERCENT/COLORS_COUNT_FOR_QUANTING
CELLS: ratio = compress_1_time / compress_2_time
      3     4     5     6     7     8     9     10    11    12    13    14    15    16    17    18    19    20    21    22    23    24    25    26    27    28    29    30    31    32    33    34    35    36    
40    1.0   1.0   0.5   0.4   0.5   0.5   1.0   1.0   1.0   1.0   1.0   1.0   1.0   1.0   0.5   0.7   0.4   0.5   0.5   0.7   0.8   0.9   0.9   0.7   0.7   0.6   0.7   0.7   0.7   0.7   0.8   0.9   0.8   0.8   
50    1.0   1.0   0.6   0.4   0.5   0.5   1.0   1.0   1.0   1.0   1.0   2.5   1.0   1.0   0.5   0.6   0.6   0.6   0.6   0.6   0.6   0.8   0.8   0.5   0.4   0.5   0.4   0.4   0.5   0.5   0.8   0.8   0.6   0.8   
60    1.0   1.0   0.6   0.5   0.6   0.5   1.0   1.0   3.0   2.4   2.2   2.4   1.0   2.5   0.7   0.6   0.7   0.7   0.6   0.7   0.7   0.6   0.6   0.6   0.6   0.6   0.5   0.5   0.7   0.5   0.8   0.9   0.8   0.8   
70    1.0   1.0   0.6   0.5   0.7   0.5   3.0   1.0   3.0   2.3   2.2   2.1   2.2   2.8   0.7   0.7   0.8   0.9   0.9   0.7   0.7   0.8   0.8   0.8   0.8   0.9   0.8   0.8   0.8   0.8   0.8   0.8   0.7   0.8   
80    1.0   1.0   0.7   0.6   0.7   0.7   2.3   2.1   2.4   2.5   2.4   2.4   2.3   2.3   0.6   0.8   0.7   0.7   0.7   0.8   0.7   0.8   0.7   0.7   0.7   0.7   0.6   0.6   0.6   0.7   0.7   0.6   0.6   0.6   
90    1.0   1.0   0.7   0.6   0.8   0.7   2.3   2.7   2.4   2.6   2.3   2.6   2.3   2.5   0.8   0.8   1.4   0.4   0.8   0.8   1.4   0.5   0.9   0.8   1.4   0.5   0.8   0.8   1.2   0.5   0.5   0.5   0.6   0.5   

    MAX_CHUNK_LENGTH = 16384
    MIN_CHUNK_LENGTH = 256
    OPTIMAL_CHUNK_COUNT = 8
    
      3     4     5     6     7     8     9     10    11    12    13    14    15    16    17    18    19    20    21    22    23    24    25    26    27    28    29    30    31    32    33    34    35    36    
40    1.0   1.0   0.5   0.4   0.4   0.4   1.0   1.0   1.0   1.0   1.0   1.0   1.0   1.0   0.5   0.6   0.4   0.7   0.5   1.0   1.0   1.0   0.6   0.5   0.5   0.5   0.5   0.6   0.6   0.6   0.6   0.6   0.7   0.8   
50    1.0   1.0   0.4   0.4   0.5   1.0   1.0   1.0   1.0   1.0   1.0   1.0   1.0   1.0   0.5   0.4   0.5   0.5   0.5   0.5   0.5   0.8   0.6   0.4   0.4   0.4   0.4   0.4   0.4   0.4   0.7   0.7   0.7   0.7   
60    1.0   1.0   0.5   0.4   0.5   0.4   1.0   1.0   2.1   2.0   2.2   2.7   2.4   2.6   0.5   0.5   0.5   0.5   0.5   0.5   0.5   0.5   0.5   0.5   0.4   0.5   0.4   0.4   0.4   0.4   0.6   0.6   0.6   0.6   
70    1.0   1.0   0.5   0.4   0.5   0.5   2.1   2.2   2.7   2.3   2.3   2.5   2.4   2.5   0.5   0.5   0.6   0.6   0.6   0.5   0.5   0.6   0.5   0.5   0.5   0.5   0.5   0.5   0.5   0.5   0.7   0.7   0.7   0.6   
80    1.0   1.0   0.5   0.5   0.5   0.4   2.3   2.0   2.6   2.2   2.7   2.5   2.3   2.5   0.6   0.6   0.6   0.6   0.7   0.7   0.7   0.7   0.7   0.6   0.7   0.8   0.6   0.6   0.6   0.6   0.7   0.6   0.7   0.7   
90    1.0   1.0   0.5   0.5   0.6   0.6   2.7   2.3   3.0   2.4   2.3   2.4   2.4   2.8   0.6   0.8   0.8   0.8   0.8   0.8   0.8   0.9   0.8   0.8   0.8   0.9   0.8   0.8   0.8   0.8   0.5   0.5   0.4   0.5   

OPTIMAL_CHUNK_COUNT = 12

      3     4     5     6     7     8     9     10    11    12    13    14    15    16    17    18    19    20    21    22    23    24    25    26    27    28    29    30    31    32    33    34    35    36    
40    1.0   1.0   0.4   1.0   0.4   0.4   1.0   1.0   1.0   1.0   1.0   1.0   1.0   1.0   0.4   0.5   0.4   0.4   0.4   0.6   0.5   0.6   0.6   0.5   0.5   0.5   0.6   0.5   0.6   0.6   0.6   0.6   0.7   0.6   
50    1.0   1.0   0.4   0.4   0.4   0.4   1.0   1.0   1.0   1.0   1.0   1.0   1.0   2.2   0.4   0.4   0.5   0.5   0.4   0.4   0.4   0.5   0.6   0.7   0.4   0.3   0.2   0.4   0.4   0.4   0.6   0.7   0.6   0.6   
60    1.0   1.0   0.5   0.6   0.4   0.4   1.0   1.0   2.8   2.5   2.3   2.4   2.2   2.1   0.5   0.4   0.5   0.4   0.8   0.5   0.4   0.5   0.4   0.4   0.4   0.4   0.5   0.4   0.4   0.3   0.6   0.6   0.6   0.6   
70    1.0   1.0   0.4   0.5   0.5   0.4   1.0   2.1   2.7   2.3   2.2   2.2   2.3   2.4   0.5   0.5   0.7   0.5   0.4   0.5   0.5   0.5   0.5   0.5   0.5   0.5   0.5   0.5   0.5   0.5   0.6   0.6   0.6   0.6   
80    1.0   1.0   0.6   0.4   0.5   0.4   2.8   2.1   2.5   2.2   2.5   2.5   2.1   2.6   0.4   0.6   0.7   0.6   0.6   0.7   0.7   0.5   0.6   0.6   0.6   0.7   0.5   0.6   0.6   0.6   0.6   0.5   0.5   0.6   
90    1.0   1.0   0.5   0.4   0.5   0.5   2.5   2.1   2.5   2.6   2.1   2.3   2.5   2.6   0.6   0.6   0.8   0.6   0.7   0.8   0.8   0.7   0.7   0.8   0.8   0.8   0.7   0.7   0.7   0.7   0.4   0.5   0.4   0.4 
OPTIMAL_CHUNK_COUNT = 14


"""
