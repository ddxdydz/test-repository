from PIL import Image

from basic.image.quanting.BaseQuantizer import BaseQuantizer


class GrayscaleQuantizer(BaseQuantizer):
    """Квантователь в оттенки серого"""

    def quantize(self, img: Image) -> [int]:
        """Квантование в оттенки серого"""
        if img.mode != 'RGB':
            img = img.convert('RGB')

        width, height = img.size
        pixels_data = img.load()
        quants = []

        for row in range(height):
            for col in range(width):
                r, g, b = pixels_data[col, row]
                # Используем средневзвешенное значение для лучшего восприятия
                brightness = int(0.299 * r + 0.587 * g + 0.114 * b)
                quants.append(self.value_to_quant(brightness))

        return quants

    def dequantize(self, quants: [int], width: int, height: int) -> Image:
        """Восстановление черно-белого изображения"""
        if len(quants) != width * height:
            raise ValueError("Quants array size doesn't match image dimensions")

        img = Image.new('RGB', (width, height))
        pixels_data = img.load()

        index = 0
        for row in range(height):
            for col in range(width):
                quant_val = quants[index]
                pixel_value = self.quant_to_value(quant_val)
                pixels_data[col, row] = (pixel_value, pixel_value, pixel_value)
                index += 1

        return img


if __name__ == "__main__":
    input_image = Image.open(r"C:\Users\UserLog.ru\PycharmProjects\regular\basic\image\data\v7.png")
    gray_quant = GrayscaleQuantizer(colors=8)
    gray_quants = gray_quant.quantize(input_image)
    gray_restored = gray_quant.dequantize(gray_quants, input_image.width, input_image.height)
    gray_restored.show()
