import colorsys
from typing import List, Tuple


def generate_palette(colors: int) -> List[Tuple[int, int, int]]:
    """
    Генерирует цветовую палитру
    """
    palette = [
        (255, 255, 255), (0, 0, 0), (255, 0, 0), (0, 255, 0),
        (0, 0, 255), (128, 128, 128), (255, 255, 0), (255, 0, 255),
        (0, 255, 255), (192, 192, 192), (64, 64, 64), (128, 0, 0),
        (0, 128, 0), (0, 0, 128), (220, 220, 220), (105, 105, 105),
        (255, 128, 128), (255, 64, 64), (192, 0, 0), (128, 64, 64),
        (128, 255, 128), (64, 255, 64), (0, 192, 0), (64, 128, 64),
        (128, 128, 255), (64, 64, 255), (0, 0, 192), (64, 64, 128),
        (255, 128, 0), (255, 0, 128), (128, 255, 0), (0, 255, 128),
        (128, 0, 255), (0, 128, 255), (255, 128, 255), (128, 255, 255),
        (139, 69, 19), (160, 82, 45), (210, 105, 30), (205, 133, 63),
        (255, 182, 193), (255, 218, 185), (230, 230, 250), (240, 255, 240)
    ]

    num = 0
    while len(palette) < colors:
        num += 1
        hue = num / 1000  # от 0 до 1
        saturation = 0.7 + 0.3 * (num % 3) / 2  # варьируем насыщенность
        value = 0.5 + 0.5 * (num % 2)  # варьируем яркость
        r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
        color = (int(r * 255), int(g * 255), int(b * 255))
        if color not in palette:
            palette.append(color)

    return palette[:colors]


if __name__ == "__main__":
    from time import time
    for i in range(2, 256):
        s = time()
        p = generate_palette(i)
        is_correct = i == len(set(p))
        print(f"{i}, {is_correct}, {time() - s:.6f}")
        if not is_correct:
            print(i, len(set(p)))
            input()
