from PIL import Image

from basic.image.quanting.BaseQuantizer import BaseQuantizer


class RGBQuantizer(BaseQuantizer):
    """Квантователь для цветных RGB изображений"""

    def __init__(self, colors_per_channel=3):
        """
        Инициализация RGB квантователя

        Args:
            colors_per_channel: количество цветов на каждый канал (R, G, B)
        """
        super().__init__(colors_per_channel)
        self.total_colors = colors_per_channel ** 3

    def quantize(self, img: Image, return_single_array: bool = False):
        """
        Квантование RGB изображения

        Args:
            return_single_array: если True, возвращает упакованный массив
        """
        if img.mode != 'RGB':
            img = img.convert('RGB')

        width, height = img.size
        pixels_data = img.load()

        if return_single_array:
            return self._quantize_to_single_array(width, height, pixels_data)
        else:
            return self._quantize_to_tuples(width, height, pixels_data)

    def _quantize_to_tuples(self, width, height, pixels_data) -> [tuple]:
        """Квантование в кортежи (r, g, b)"""
        quantized_pixels = []
        for row in range(height):
            for col in range(width):
                r, g, b = pixels_data[col, row]
                r_quant = self.value_to_quant(r)
                g_quant = self.value_to_quant(g)
                b_quant = self.value_to_quant(b)
                quantized_pixels.append((r_quant, g_quant, b_quant))
        return quantized_pixels

    def _quantize_to_single_array(self, width, height, pixels_data) -> [int]:
        """Квантование в упакованный массив"""
        single_array = []
        for row in range(height):
            for col in range(width):
                r, g, b = pixels_data[col, row]
                r_quant = self.value_to_quant(r)
                g_quant = self.value_to_quant(g)
                b_quant = self.value_to_quant(b)
                # Упаковываем три значения в одно число
                pixel_value = (r_quant * (self.COLORS ** 2) +
                               g_quant * self.COLORS +
                               b_quant)
                single_array.append(pixel_value)
        return single_array

    def dequantize(self, quantized_data, width: int, height: int) -> Image:
        """
        Восстановление изображения из квантованных данных

        Args:
            quantized_data: может быть списком кортежей или упакованным массивом
        """
        if len(quantized_data) != width * height:
            raise ValueError("Quantized data size doesn't match image dimensions")

        # Определяем тип данных
        is_single_array = False if isinstance(quantized_data[0], tuple) else True
        return self._dequantize(quantized_data, width, height, is_single_array)

    def _dequantize(self, quantized_data, width, height, is_single_array: bool = False) -> Image:
        img = Image.new('RGB', (width, height))
        pixels_data = img.load()

        index = 0
        for row in range(height):
            for col in range(width):
                if is_single_array:
                    packed_value = quantized_data[index]
                    # Распаковываем значения
                    r_quant = packed_value // (self.COLORS ** 2)
                    remainder = packed_value % (self.COLORS ** 2)
                    g_quant = remainder // self.COLORS
                    b_quant = remainder % self.COLORS
                else:
                    r_quant, g_quant, b_quant = quantized_data[index]
                r_val = self.quant_to_value(r_quant)
                g_val = self.quant_to_value(g_quant)
                b_val = self.quant_to_value(b_quant)
                pixels_data[col, row] = (r_val, g_val, b_val)
                index += 1

        return img

    def quantize_to_bytes(self, img: Image) -> bytes:
        ...

    def dequantize_from_bytes(self, quantize_data: bytes, width: int, height: int) -> Image:
        ...

    def get_color_palette(self) -> list:
        """Получение полной RGB палитры"""
        palette = []
        for r in range(self.COLORS):
            for g in range(self.COLORS):
                for b in range(self.COLORS):
                    palette.append((
                        self.quant_to_value(r),
                        self.quant_to_value(g),
                        self.quant_to_value(b)
                    ))
        return palette

    @staticmethod
    def get_compression_ratio(original_img: Image, use_single_array: bool = True) -> float:
        """Коэффициент сжатия для RGB"""
        original_size = original_img.width * original_img.height * 3  # 3 байта на пиксель

        if use_single_array:
            quantized_size = original_img.width * original_img.height  # 1 число на пиксель
        else:
            quantized_size = original_img.width * original_img.height * 3  # 3 числа на пиксель

        return original_size / quantized_size


if __name__ == "__main__":
    img = Image.open(r"C:\Users\UserLog.ru\PycharmProjects\regular\basic\image\data\v4.png")
    rgb_quant = RGBQuantor(colors_per_channel=2)

    # Цветное квантование (кортежи)
    rgb_quants_tuples = rgb_quant.quantize(img, return_single_array=False)
    rgb_restored = rgb_quant.dequantize(rgb_quants_tuples, img.width, img.height)

    # Цветное квантование (упакованный массив)
    # rgb_quants_single = rgb_quant.quantize(img, return_single_array=True)
    # rgb_restored = rgb_quant.dequantize(rgb_quants_single, img.width, img.height)

    # Получение информации
    rgb_palette = rgb_quant.get_color_palette()
    rgb_compression = rgb_quant.get_compression_ratio(img)
    print(f"RGB palette size: {len(rgb_palette)} colors")
    print(f"RGB compression: {rgb_compression:.2f}:1")

    rgb_restored.show()
