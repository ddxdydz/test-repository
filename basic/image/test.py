from pathlib import Path
from time import time

import numpy as np
from PIL import Image

from basic.image.__all_tools import *

img_path = Path(__file__).parent / "data" / "v10.png"
original_img = Image.open(img_path)
img_array = np.array(original_img, dtype=np.uint8)

resizer = CVResizer(0.6)
quantizer = GrayQuantizer(3)
# quantizer = CombQuantizer(8)
packer = CombPacker(quantizer.bits_per_color)
compressor = LZMACompressor()

_start_time = time()
resized = resizer.resize(img_array)
print("resized".ljust(20), time() - _start_time)
_start_time = time()
quantized = quantizer.quantize(resized)
print("quantized".ljust(20), time() - _start_time)
_start_time = time()
packed = packer.pack_array(quantized)
print("packed".ljust(20), time() - _start_time)
_start_time = time()
compressed = compressor.compress(packed)
print("compressed".ljust(20), time() - _start_time, len(compressed) // 1024, "KB", len(compressed), "B")
_start_time = time()
decompressed = compressor.decompress(compressed)
print("decompressed".ljust(20), time() - _start_time)
_start_time = time()
unpacked = packer.unpack_array(decompressed)
print("unpacked".ljust(20), time() - _start_time)
_start_time = time()
dequantized = quantizer.dequantize(unpacked)
print("dequantized".ljust(20), time() - _start_time)
_start_time = time()
desized = resizer.desize(dequantized)
print("desized".ljust(20), time() - _start_time)

Image.fromarray(desized).show()
