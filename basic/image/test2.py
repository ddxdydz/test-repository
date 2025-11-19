from pathlib import Path
from time import time

import numpy as np
from PIL import Image

from basic.image.__all_tools import *

# LZMA не используется, всегда самый медленный

img_path = Path(__file__).parent / "data" / "v9.png"  # не влияет, влияют только scale и colors
compressor_bz2 = BZ2Compressor()
compressor_zlb = ZlibCompressor()

resizer = CVResizer(0.5)  # чем больше, тем дольше BZ2
quantizer = GrayQuantizer(16)  # чем больше, тем быстрее BZ2 (в разы), только для Gray
packer = CombPacker(quantizer.bits_per_color)
resized = resizer.resize(np.array(Image.open(img_path), dtype=np.uint8))
quantized = quantizer.quantize(resized)
packed = packer.pack_array(quantized)

_start_time = time()
compressed = compressor.compress(packed)
print(f"{compressor.name}".ljust(30),
      f"{time() - _start_time:.6f}", len(compressed) // 1024, "KB", len(compressed), "B")

_start_time = time()
compressed = compressor.compress(packed)
print(f"{compressor.name}".ljust(30),
      f"{time() - _start_time:.6f}", len(compressed) // 1024, "KB", len(compressed), "B")
