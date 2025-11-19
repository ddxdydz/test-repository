from pathlib import Path
from time import time

import numpy as np
from PIL import Image

from basic.image.__all_tools import *

# LZMA не используется, всегда самый медленный

img_path = Path(__file__).parent / "data" / "v9.png"  # не влияет, влияют только scale и colors
resizer = CVResizer(0.5)  # чем больше, тем дольше BZ2
quantizer = GrayQuantizer(16)  # чем больше, тем быстрее BZ2 (в разы), только для Gray
# quantizer = CombQuantizer(8)
packer = CombPacker(quantizer.bits_per_color)

_start_time = time()
resized = resizer.resize(np.array(Image.open(img_path), dtype=np.uint8))
print("resized".ljust(20), f"{time() - _start_time:.6f}")
_start_time = time()
quantized = quantizer.quantize(resized)
print("quantized".ljust(20), f"{time() - _start_time:.6f}")
_start_time = time()
packed = packer.pack_array(quantized)
print("packed".ljust(20), f"{time() - _start_time:.6f}")

_start_time = time()
compressor = BZ2Compressor()  # нестабильный, иногда самый быстрый (v9, 0.9, 3)
compressed = compressor.compress(packed)
print(f"{compressor.name}".ljust(30),
      f"{time() - _start_time:.6f}", len(compressed) // 1024, "KB", len(compressed), "B")
"""
CW(BZ2Compressor)              0.005699 10 KB 10347 B
CW(ZlibCompressor)             0.010401 9 KB 9506 B
"""
_start_time = time()
compressor = ZlibCompressor()  # стабильней, часто самый быстрый  (v9, 0.5, 7), всегда лучшая сжимаемость
compressed = compressor.compress(packed)
print(f"{compressor.name}".ljust(30),
      f"{time() - _start_time:.6f}", len(compressed) // 1024, "KB", len(compressed), "B")

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

Image.fromarray(desized).show()
