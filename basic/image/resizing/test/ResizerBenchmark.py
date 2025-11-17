from pathlib import Path
from time import time
from typing import List

import numpy as np
from PIL import Image

from basic.image.resizing.ABC_ImageResizer import ImageResizer, ResizeMethod


class ResizerBenchmark:
    TEMP_PATH = Path(__file__).parent.parent.parent / "resizing" / "test" / "temp_data"
    METHODS = [ResizeMethod.NEAREST, ResizeMethod.AREA, ResizeMethod.BILINEAR,
               ResizeMethod.BICUBIC, ResizeMethod.LANCZOS, ResizeMethod.LINEAR_EXACT,
               ResizeMethod.NEAREST_EXACT]

    @staticmethod
    def save_resized_images(resizer: ImageResizer, img_path: Path, scale=None):
        if scale is not None:
            resizer.reset_scale(scale)

        Image.open(img_path).save(f"{ResizerBenchmark.TEMP_PATH}\\0{img_path.name[img_path.name.rfind("."):]}")
        array = np.array(Image.open(img_path), dtype=np.uint8)

        resizer.reset_original_size((array.shape[1], array.shape[0]))

        for i in range(len(ResizerBenchmark.METHODS)):
            method = ResizerBenchmark.METHODS[i]
            resizer.reset_method(method)
            res_img = Image.fromarray(resizer.desize(resizer.resize(array)))
            res_img.save(
                f"{ResizerBenchmark.TEMP_PATH}\\{i + 1} {method.name}{img_path.name[img_path.name.rfind("."):]}")

    @staticmethod
    def _test_resize(resizer: ImageResizer, img_array: np.array, iterations: int) -> float:
        total_resize_times = []
        for _ in range(iterations):
            start = time()
            resizer.resize(img_array)
            total_resize_times.append(time() - start)

        return float(np.mean(total_resize_times))

    @staticmethod
    def _test_desize(resizer: ImageResizer, img_array: np.array, iterations: int) -> float:
        total_desize_times = []
        resized = resizer.resize(img_array)
        for _ in range(iterations):
            start = time()
            resizer.desize(resized)
            total_desize_times.append(time() - start)
        return float(np.mean(total_desize_times))

    @staticmethod
    def test(resizers: List[ImageResizer], img_path: Path, iterations: int = 100):
        img_array = np.array(Image.open(img_path), dtype=np.uint8)

        print(img_path.name, img_array.shape, img_array.size)
        print(str().rjust(20), *[str(m.name).rjust(10, ' ') for m in ResizerBenchmark.METHODS], sep="\t")

        for resizer in resizers:
            resizer.reset_original_size((img_array.shape[1], img_array.shape[0]))

            print(f"{resizer.name}   ".rjust(20))

            # Resize
            print(f"resize(sec)".rjust(20), end="\t")
            resize_times = []
            for method in ResizerBenchmark.METHODS:
                resizer.reset_method(method)
                resize_time = ResizerBenchmark._test_resize(resizer, img_array, iterations)
                resize_times.append(resize_time)
                print(f"{resize_time:.6f}".rjust(10), end="\t")
            print(f"{float(np.mean(resize_times)):.6f}")

            # Desize
            print(f"desize(sec)".rjust(20), end="\t")
            desize_times = []
            for method in ResizerBenchmark.METHODS:
                resizer.reset_method(method)
                desize_time = ResizerBenchmark._test_desize(resizer, img_array, iterations)
                desize_times.append(desize_time)
                print(f"{desize_time:.6f}".rjust(10), end="\t")
            print(f"{float(np.mean(desize_times)):.6f}")


if __name__ == "__main__":
    from basic.image.resizing.CVResizer import CVResizer
    from basic.image.resizing.PILResizer import PILResizer

    path = Path(__file__).parent.parent.parent / "data" / "v10.png"
    ResizerBenchmark.save_resized_images(CVResizer(0.6), path)
    ResizerBenchmark.test([CVResizer(), PILResizer()], path, 400)
