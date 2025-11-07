from PIL import Image

from basic.image.compression.ImageCompressor import ImageCompressor, CompressionAlgorithm, QuantizationMethod


class ImageCompressorLZMAGS4(ImageCompressor):
    def __init__(self):
        super().__init__(CompressionAlgorithm.LZMA.value, QuantizationMethod.GRAYSCALE.value, 4)


if __name__ == "__main__":
    input_image = Image.open(r"C:\Users\UserLog.ru\PycharmProjects\regular\basic\image\data\v4.png")
    compressor = ImageCompressorLZMAGS4()
    compress_data, _ = compressor.compress(input_image)
    print(len(compress_data) // 1024, "KB")
    decomp_imp = compressor.decompress(compress_data, input_image.size)
    decomp_imp.show()
