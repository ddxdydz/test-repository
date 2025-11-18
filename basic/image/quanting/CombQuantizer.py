import bz2
import os
import pickle
from pathlib import Path

import numpy as np

from basic.image.quanting.ABC_Quantizer import Quantizer
from basic.image.quanting.tools.generate_soft_palette import generate_soft_palette


class CombQuantizer(Quantizer):
    CACHE_DIR_PATH = Path(__file__).parent / "cache_comb_lut"

    def __init__(self, colors: int = 4):
        os.makedirs(self.CACHE_DIR_PATH, exist_ok=True)

        self._palette_rbg = np.empty(1, dtype=np.int8)
        self._palette_rbg_int32 = np.empty(1, dtype=np.int32)
        self._quant_palette_lut = np.empty(1, dtype=np.int8)
        self._dequant_palette_lut = np.empty(1, dtype=np.int32)

        super().__init__(2 ** (colors - 1).bit_length())

        # print(list(self._palette_rbg))
        # print(list(self._palette_rbg_int32))
        # print(sorted(set(self._quant_palette_lut)))
        # print(sorted(set(self._dequant_palette_lut)))

    def set_colors(self, colors: int):
        super().set_colors(colors)
        self._generate_palette()
        self._generate_luts()

    def _generate_palette(self):
        self._palette_rbg = np.array(sorted(generate_soft_palette(self.COLORS)), dtype=np.uint8)

        array_flat = self._palette_rbg.flatten()
        values_per_dtype = 3
        dtype = np.uint32

        padded_length = ((array_flat.size + (values_per_dtype - 1)) // values_per_dtype) * values_per_dtype
        if padded_length > array_flat.size:
            padded = np.empty(padded_length, dtype=dtype)
            padded[:array_flat.size] = array_flat
            padded[array_flat.size:] = 0
        else:
            padded = array_flat.astype(dtype)

        self._palette_rbg_int32 = (padded[0::3] << 16) | (padded[1::3] << 8) | padded[2::3]

    def _value_to_palette_quant(self, value: int) -> int:
        r = ((value >> 16) & 0xFF)
        g = ((value >> 8) & 0xFF)
        b = (value & 0xFF)

        value_rgb = np.array([r, g, b])

        distances = np.sum((self._palette_rbg - value_rgb) ** 2, axis=1)
        return int(np.argmin(distances))

    def _quant_to_palette_value(self, quant: int) -> int:
        return int(self._palette_rbg_int32[quant])

    def _get_cache_filename(self) -> Path:
        return self.CACHE_DIR_PATH / f"lut_{self.COLORS}.cl"

    def _generate_luts(self):
        cache_file = self._get_cache_filename()

        if os.path.exists(cache_file):
            with open(cache_file, 'rb') as f:
                decompressed = bz2.decompress(f.read())
                self._quant_palette_lut, self._dequant_palette_lut = pickle.loads(decompressed)
        else:
            print(f"Generating new LUTs for {self.COLORS} colors...")
            indices = np.arange(16777216, dtype=np.uint32)

            quant_vectorized = np.vectorize(self._value_to_palette_quant)
            dequant_vectorized = np.vectorize(self._quant_to_palette_value)

            self._quant_palette_lut = quant_vectorized(indices).astype(np.uint8)
            self._dequant_palette_lut = dequant_vectorized(np.minimum(indices, self.COLORS - 1)).astype(np.uint32)

            with open(cache_file, 'wb') as f:
                data = pickle.dumps((self._quant_palette_lut, self._dequant_palette_lut))
                compressed = bz2.compress(data)
                f.write(compressed)
            print(f"LUTs saved to {cache_file}")

    def quantize(self, image: np.ndarray) -> np.ndarray:
        # rgb                --shift-->  rbg_int32   --lut---->     palette_index

        if len(image.shape) != 3:
            raise ValueError(f"quantize: len(image.shape) = {len(image.shape)} != 3")
        if image.shape[2] != 3:
            if image.shape[2] == 4:
                image = image[:, :, :3]
            else:
                raise ValueError(f"quantize: image.shape[2] = {image.shape[2]} not in [3, 4]")

        image_shape = image.shape
        values_per_dtype = 3
        dtype = np.uint32
        array_flat = image.flatten().astype(dtype=dtype)

        padded_length = ((array_flat.size + (values_per_dtype - 1)) // values_per_dtype) * values_per_dtype
        if padded_length > array_flat.size:
            padded = np.empty(padded_length, dtype=dtype)
            padded[:array_flat.size] = array_flat
            padded[array_flat.size:] = 0
        else:
            padded = array_flat.astype(dtype)

        image = (padded[0::3] << 16) | (padded[1::3] << 8) | padded[2::3]
        duantized_image = self._quant_palette_lut[image]

        return duantized_image.reshape((image_shape[0], image_shape[1]))

    def dequantize(self, quantized_image: np.ndarray) -> np.ndarray:
        # palette_index      --lut---->  rbg_int32   --shift-->     rgb

        one_num_rgb_image = self._dequant_palette_lut[quantized_image]
        one_num_rgb_image_flatten = one_num_rgb_image.flatten()
        rgb_image_flatten = np.zeros(one_num_rgb_image.size * 3, dtype=np.uint8)
        rgb_image_flatten[0::3] = (one_num_rgb_image_flatten >> 16) & 0b11111111
        rgb_image_flatten[1::3] = (one_num_rgb_image_flatten >> 8) & 0b11111111
        rgb_image_flatten[2::3] = one_num_rgb_image_flatten & 0b11111111
        rgb_image = rgb_image_flatten.reshape((quantized_image.shape[0], quantized_image.shape[1], 3))

        return rgb_image


if __name__ == "__main__":
    quantizer = CombQuantizer(2 ** 1)
    quantizer = CombQuantizer(2 ** 2)
    quantizer = CombQuantizer(2 ** 3)
    quantizer = CombQuantizer(2 ** 4)
    quantizer = CombQuantizer(2 ** 5)
    quantizer = CombQuantizer(2 ** 6)
    quantizer = CombQuantizer(2 ** 7)
    quantizer = CombQuantizer(2 ** 8)

    from PIL import Image
    img_path = Path(__file__).parent.parent / "data" / "v4.png"
    original_img = Image.open(img_path)
    img_array = np.array(original_img, dtype=np.uint8)
    Image.fromarray(quantizer.dequantize(quantizer.quantize(img_array))).show()

"""
256 MB
bz2 compress 79.99023222923279
bz2 decompress 5.219536066055298
10 KB
lzma compress 12.713189363479614
lzma decompress 1.9897534847259521
38 KB
zlib compress 3.7556722164154053
zlib decompress 0.733863115310669
382 KB

    from time import time
    import bz2
    import lzma
    import zlib

    with open(quantizer._get_cache_filename(), 'rb') as f:
        file_bytes = f.read()
    print(len(file_bytes) // 1024 // 1024, "MB")

    s_time = time()
    file_bytes_compress = bz2.compress(file_bytes)
    print("bz2 compress", time() - s_time)
    s_time = time()
    bz2.decompress(file_bytes_compress)
    print("bz2 decompress", time() - s_time)
    print(len(file_bytes_compress) // 1024, "KB")

    s_time = time()
    file_bytes_compress = lzma.compress(file_bytes)
    print("lzma compress", time() - s_time)
    s_time = time()
    lzma.decompress(file_bytes_compress)
    print("lzma decompress", time() - s_time)
    print(len(lzma.compress(file_bytes)) // 1024, "KB")

    s_time = time()
    file_bytes_compress = zlib.compress(file_bytes)
    print("zlib compress", time() - s_time)
    s_time = time()
    zlib.decompress(file_bytes_compress)
    print("zlib decompress", time() - s_time)
    print(len(zlib.compress(file_bytes)) // 1024, "KB")
"""
