from typing import List, Tuple

from basic.image.quanting.tools.generate_palette import generate_palette
from basic.image.quanting.tools.soft_color_rgb import soft_color_rgb


def generate_soft_palette(colors: int) -> List[Tuple[int, int, int]]:
    palette = generate_palette(colors)
    if colors > 42:
        return palette
    return [soft_color_rgb(rgb) for rgb in palette]


if __name__ == "__main__":
    from time import time
    for i in range(2, 256):
        s = time()
        p = generate_soft_palette(i)
        is_correct = i == len(set(p))
        print(f"{i}, {is_correct}, {time() - s:.6f}")
        if not is_correct:
            print(i, len(set(p)))
            input()
