from pathlib import Path
from time import time
from typing import Tuple, Dict, Optional

import numpy as np
from PIL import Image
from mss import mss

from basic.image.compression.base_compressors import BZ2Compressor
from basic.image.difference.GrayscaleDifferenceHandler import GrayscaleDifferenceHandler
from basic.image.packing.NoTampingPacker import NoTampingPacker
from basic.image.quanting.GrayQuantizer import GrayQuantizer
from basic.image.resizing.CVResizerIntScale import CVResizerIntScale


class ToolsManager:
    def __init__(self, width: int, height: int, colors: int, scale_percent: int):
        self.name = self.__class__.__name__
        self.parameters = width, height, colors, scale_percent
        self._resizer = CVResizerIntScale(scale_percent=scale_percent, original_size=(width, height))
        self._quantizer = GrayQuantizer(colors)
        self._packer = NoTampingPacker(colors)
        self._compressor = BZ2Compressor()
        self._difference_handler = GrayscaleDifferenceHandler(colors, scale_percent, shape=(height, width))

    def apply(self, difference: np.ndarray) -> None:
        self._difference_handler.apply_difference(difference)

    @staticmethod
    def open(path: Optional[Path] = None):
        _start_time = time()
        if path is None:
            with mss() as sct:
                image_to_encode = sct.grab(sct.monitors[1])
        else:
            image_to_encode = Image.open(path)
        time_to_open = time() - _start_time
        return time_to_open, image_to_encode

    @staticmethod
    def convert(image_to_convert) -> Tuple[float, np.ndarray]:
        _start_time = time()
        data = np.asarray(image_to_convert, dtype=np.uint8)
        if len(data.shape) == 3 and data.shape[2] == 4:
            data = data[:, :, :3]
        time_to_convert = time() - _start_time
        return time_to_convert, data

    def resize(self, image_array: np.ndarray) -> Tuple[float, np.ndarray]:
        _start_time = time()
        data = self._resizer.resize(image_array)
        time_to_resize = time() - _start_time
        return time_to_resize, data

    def desize(self, image_array: np.ndarray) -> Tuple[float, np.ndarray]:
        _start_time = time()
        data = self._resizer.desize(image_array)
        time_to_desize = time() - _start_time
        return time_to_desize, data

    def quantize(self, image_array: np.ndarray) -> Tuple[float, np.ndarray]:
        _start_time = time()
        data = self._quantizer.quantize(image_array)
        time_to_quantize = time() - _start_time
        return time_to_quantize, data

    def dequantize(self, image_array: np.ndarray) -> Tuple[float, np.ndarray]:
        _start_time = time()
        data = self._quantizer.dequantize(image_array)
        time_to_dequantize = time() - _start_time
        return time_to_dequantize, data

    def compute_difference(self, image_array: np.ndarray) -> Tuple[float, np.ndarray]:
        _start_time = time()
        data = self._difference_handler.compute_difference(image_array)
        time_to_compute_difference = time() - _start_time
        return time_to_compute_difference, data

    def apply_difference(self, difference: np.ndarray) -> Tuple[float, np.ndarray]:
        _start_time = time()
        data = self._difference_handler.apply_difference(difference)
        time_to_apply_difference = time() - _start_time
        return time_to_apply_difference, data

    def pack(self, image_array: np.ndarray) -> Tuple[float, bytes]:
        _start_time = time()
        data = self._packer.pack_array(image_array)
        time_to_pack = time() - _start_time
        return time_to_pack, data

    def unpack(self, data: bytes) -> Tuple[float, np.ndarray]:
        _start_time = time()
        data = self._packer.unpack_array(data)
        time_to_unpack = time() - _start_time
        return time_to_unpack, data

    def compress(self, data_to_compress: bytes) -> Tuple[float, bytes]:
        _start_time = time()
        data = self._compressor.compress(data_to_compress)
        time_to_compress = time() - _start_time
        return time_to_compress, data

    def decompress(self, data_to_compress: bytes) -> Tuple[float, bytes]:
        _start_time = time()
        data = self._compressor.decompress(data_to_compress)
        time_to_decompress = time() - _start_time
        return time_to_decompress, data

    def encode_image(self, path: Optional[Path] = None) -> Tuple[Dict, np.ndarray, bytes]:
        _start_time = time()
        encode_stats = dict()
        encode_stats["time_to_open"], image_to_encode = self.open(path)
        encode_stats["time_to_convert"], converted = self.convert(image_to_encode)
        encode_stats["time_to_resize"], data = self.resize(converted)
        encode_stats["time_to_quantize"], data = self.quantize(data)
        encode_stats["time_to_compute_difference"], difference = self.compute_difference(data)
        encode_stats["time_to_pack"], data = self.pack(difference)
        encode_stats["time_to_compress"], compressed = self.compress(data)
        encode_stats["total_time"] = time() - _start_time
        encode_stats["encoded_size"] = len(compressed)
        return encode_stats, difference, compressed

    def decode_image(self, encoded_difference: bytes) -> Tuple[Dict, np.ndarray]:
        _start_time = time()
        decode_stats = dict()
        decode_stats["time_to_decompress"], data = self.decompress(encoded_difference)
        decode_stats["time_to_unpack"], data = self.unpack(data)
        decode_stats["time_to_apply_difference"], data = self.apply_difference(data)
        decode_stats["time_to_dequantize"], data = self.dequantize(data)
        decode_stats["time_to_desize"], result = self.desize(data)
        decode_stats["total_time"] = time() - _start_time
        decode_stats["encoded_size"] = len(encoded_difference)
        return decode_stats, result

    @staticmethod
    def print_encode_stats(encode_stats: Dict, left_indent: int = 8) -> None:
        data_to_print = [
            f"{"time_to_open".ljust(22)}{encode_stats["time_to_open"]:.6f}",
            f"{"time_to_convert".ljust(22)}{encode_stats["time_to_convert"]:.6f}",
            f"{"time_to_resize".ljust(22)}{encode_stats["time_to_resize"]:.6f}",
            f"{"time_to_quantize".ljust(22)}{encode_stats["time_to_quantize"]:.6f}",
            f"{"time_to_compute_diff".ljust(22)}{encode_stats["time_to_compute_difference"]:.6f}",
            f"{"time_to_pack".ljust(22)}{encode_stats["time_to_pack"]:.6f}",
            f"{"time_to_compress".ljust(22)}{encode_stats["time_to_compress"]:.6f}",
            f"{"total_time".ljust(22)}{encode_stats["total_time"]:.6f}",
            f"{"encoded_size".ljust(22)}{encode_stats["encoded_size"]} B"
        ]
        print(f'{left_indent * " "}{f"\n{left_indent * " "}".join(data_to_print)}')

    @staticmethod
    def print_decode_stats(decode_stats: Dict, left_indent: int = 8) -> None:
        data_to_print = [
            f"{"time_to_decompress".ljust(22)}{decode_stats["time_to_decompress"]:.6f}",
            f"{"time_to_unpack".ljust(22)}{decode_stats["time_to_unpack"]:.6f}",
            f"{"time_to_apply_diff".ljust(22)}{decode_stats["time_to_apply_difference"]:.6f}",
            f"{"time_to_dequantize".ljust(22)}{decode_stats["time_to_dequantize"]:.6f}",
            f"{"time_to_desize".ljust(22)}{decode_stats["time_to_desize"]:.6f}",
            f"{"total_time".ljust(22)}{decode_stats["total_time"]:.6f}",
            f"{"encoded_size".ljust(22)}{decode_stats["encoded_size"]} B"
        ]
        print(f'{left_indent * " "}{f"\n{left_indent * " "}".join(data_to_print)}')

    @staticmethod
    def show_decoded_image(decoded_image: np.ndarray) -> None:
        Image.fromarray(decoded_image).show()

    @staticmethod
    def print_divided_line() -> None:
        print("########################################################")


if __name__ == "__main__":
    tools_manager = ToolsManager(1279, 719, 3, 60)
    for image_name in ["ch1.jpg", "ch2.jpg", "ch3.jpg", "ch3.jpg"]:
        stats, diff, encoded = tools_manager.encode_image(Path(__file__).parent / "data" / image_name)
        tools_manager.print_divided_line()
        tools_manager.print_encode_stats(stats)
        stats, decoded = tools_manager.decode_image(encoded)
        tools_manager.print_decode_stats(stats)
    tools_manager.show_decoded_image(decoded)

    # import pyautogui
    # tools_manager = ToolsManager(*pyautogui.size(), 3, 60)
    # for _ in range(4):
    #     stats, diff, encoded = tools_manager.encode_image()
    #     tools_manager.print_divided_line()
    #     tools_manager.print_encode_stats(stats)
    #     stats, decoded = tools_manager.decode_image(encoded)
    #     tools_manager.print_decode_stats(stats)
    #     tools_manager.show_decoded_image(decoded)
