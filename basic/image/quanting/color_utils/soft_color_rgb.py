import colorsys
from typing import Tuple


def soft_color_rgb(rgb: Tuple[int, int, int], saturation_factor=0.7, lightness_factor=1.1) -> Tuple[int, int, int]:
    """
    Смягчает цвет через HSL преобразование
    rgb: tuple (r, g, b) в диапазоне 0-255
    saturation_factor: множитель насыщенности (<1 для смягчения)
    lightness_factor: множитель яркости (>1 для осветления)
    """
    r, g, b = [x / 255.0 for x in rgb]
    h, l, s = colorsys.rgb_to_hls(r, g, b)

    # Уменьшаем насыщенность и немного увеличиваем яркость
    s = min(s * saturation_factor, 1.0)
    l = min(l * lightness_factor, 1.0)

    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return int(r * 255), int(g * 255), int(b * 255)


if __name__ == "__main__":
    original_color = (0, 0, 255)
    soft_color = soft_color_rgb(original_color)
    print(f"Оригинальный: {original_color}")
    print(f"Смягченный: {soft_color}")
