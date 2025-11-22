from pathlib import Path
from time import time

import mss
import numpy as np
import pyautogui
from PIL import Image
import cv2
from basic.image.__all_tools import *

# LZMA не используется, всегда самый медленный

img_path = Path(__file__).parent / "data" / "a8.jpg"
resizer = CVResizerIntScale(60)
quantizer = GrayQuantizer(3)
# quantizer = CombQuantizer(8)
packer = NoTampingPacker(quantizer.bits_per_color)

_start_time = time()
# image = Image.open(img_path)
# image = pyautogui.screenshot()
with mss.mss() as sct:
    image = sct.grab(sct.monitors[1])
print("Image.open".ljust(20), f"{time() - _start_time:.6f}")

_start_time = time()
# img_array = cv2.imread(img_path)
img_array = np.asarray(image, dtype=np.uint8)
if len(img_array.shape) == 3 and img_array.shape[2] == 4:
    img_array = img_array[:, :, :3]
# img_array = np.array(screenshot)
print("np.array".ljust(20), f"{time() - _start_time:.6f}")

_start_time = time()
resized = resizer.resize(img_array)
print("resized".ljust(20), f"{time() - _start_time:.6f}")
_start_time = time()
quantized = quantizer.quantize(resized)
print("quantized".ljust(20), f"{time() - _start_time:.6f}")
_start_time = time()
packed = packer.pack_array(quantized)
print("packed".ljust(20), f"{time() - _start_time:.6f}")

_start_time = time()
compressor = BZ2Compressor()
compressed = compressor.compress(packed)
print(f"{compressor.name}".ljust(30),
      f"{time() - _start_time:.6f}", len(compressed) // 1024, "KB", len(compressed), "B")

# _start_time = time()
# compressor = ThreadCompressor()
# compressed = compressor.compress(packed)
# print(f"{compressor.name}".ljust(30),
#       f"{time() - _start_time:.6f}", len(compressed) // 1024, "KB", len(compressed), "B")

_start_time = time()
decompressed = compressor.decompress(compressed)
print("decompressed".ljust(20), f"{time() - _start_time:.6f}")
_start_time = time()
unpacked = packer.unpack_array(decompressed)
print("unpacked".ljust(20), f"{time() - _start_time:.6f}")
_start_time = time()
dequantized = quantizer.dequantize(unpacked)
print("dequantized".ljust(20), f"{time() - _start_time:.6f}")
_start_time = time()
desized = resizer.desize(dequantized)
print("desized".ljust(20), f"{time() - _start_time:.6f}")

# Image.fromarray(desized).show()
