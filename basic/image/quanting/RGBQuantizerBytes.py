from PIL import Image

from basic.image.quanting.RGBQuantizer import RGBQuantizer


class RGBQuantizerBytes(RGBQuantizer):
    def quantize_to_bytes(self, img: Image) -> bytes:
        if img.mode != 'RGB':
            img = img.convert('RGB')

        width, height = img.size
        pixels_data = img.load()

        bits_per_color = self.total_colors.bit_length()
        if bits_per_color == 0 or bits_per_color > 8:  # TODO
            raise ValueError("Невозможно преобразовать в bytes, уменьшите количество цветов для quantization.")

        # Предвычисление констант
        bits_mask = (1 << bits_per_color) - 1
        result = bytearray()
        # Обработка по 8 байт за раз для лучшей производительности
        current_byte = 0
        bits_used = 0
        # Используем локальные переменные для скорости
        append = result.append

        for row in range(height):
            for col in range(width):

                r, g, b = pixels_data[col, row]
                r_quant = self.value_to_quant(r)
                g_quant = self.value_to_quant(g)
                b_quant = self.value_to_quant(b)
                color = (r_quant * (self.COLORS ** 2) + g_quant * self.COLORS + b_quant)

                # Действия с битами
                current_byte = (current_byte << bits_per_color) | (color & bits_mask)
                bits_used += bits_per_color
                if bits_used >= 8:
                    append(current_byte >> (bits_used - 8))
                    bits_used -= 8
                    # Маска для оставшихся битов
                    current_byte &= (1 << bits_used) - 1

        # Обработка остатка
        if bits_used > 0:
            append(current_byte << (8 - bits_used))

        return bytes(result)

    def dequantize_from_bytes(self, quantization_data: bytes, width: int, height: int) -> Image:
        img = Image.new('RGB', (width, height))
        pixels_data = img.load()
        pixels_count = width * height

        bits_per_color = self.total_colors.bit_length()
        if bits_per_color == 0 or bits_per_color > 8:
            raise ValueError("Некорректная битовая глубина в данных (должно быть 1 байт на цвет)")

        # Предвычисление констант
        bits_mask = (1 << bits_per_color) - 1

        # Используем локальные переменные для скорости
        current_buffer = 0
        current_bits = 0

        color_index = 0

        for byte_val in quantization_data:
            current_buffer = (current_buffer << 8) | byte_val
            current_bits += 8

            # Извлекаем все возможные цвета из текущего буфера
            while current_bits >= bits_per_color:
                shift = current_bits - bits_per_color
                quant_value = (current_buffer >> shift) & bits_mask

                r_quant = quant_value // (self.COLORS ** 2)
                remainder = quant_value % (self.COLORS ** 2)
                g_quant = remainder // self.COLORS
                b_quant = remainder % self.COLORS
                r = self.quant_to_value(r_quant)
                g = self.quant_to_value(g_quant)
                b = self.quant_to_value(b_quant)

                row = color_index // width
                col = color_index % width
                pixels_data[col, row] = (r, g, b)
                color_index += 1
                if color_index == pixels_count:
                    break

                current_buffer &= (1 << shift) - 1
                current_bits -= bits_per_color

        return img

    def dequantize_from_bytes_to_bytes(self, quantization_data: bytes, width: int, height: int) -> bytes:
        return self.dequantize_from_bytes(quantization_data, width, height).tobytes()


if __name__ == "__main__":
    input_image = Image.open(r"C:\Users\UserLog.ru\PycharmProjects\regular\basic\image\data\v4.png")
    quant = RGBQuantizerBytes(colors_per_channel=4)

    from time import time

    start_time = time()
    gray_quants = quant.quantize_to_bytes(input_image)
    print("quantize_to_bytes", f"{time() - start_time}s", sep="\t")

    start_time = time()
    gray_quants_from_bytes = quant.dequantize_from_bytes(gray_quants, *input_image.size)
    print("dequantize_from_bytes", f"{time() - start_time}s", sep="\t")

    gray_quants_from_bytes.show()
