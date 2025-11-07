import time
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Any

from PIL import Image

from basic.image.compression.ImageCompressor import ImageCompressor
from basic.image.compression.ImageCompressorLZMAGS4 import ImageCompressorLZMAGS4


@dataclass
class CompressionResult:
    """Результат сжатия"""
    original_size: int
    compressed_size: int
    compression_time: float
    decompression_time: float
    compression_ratio: float
    algorithm: str
    quantization_method: Optional[str] = None
    resize_method: Optional[str] = None
    original_dimensions: Optional[Tuple[int, int]] = None
    processed_dimensions: Optional[Tuple[int, int]] = None
    psnr: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class CompressorAnalyzer:
    @staticmethod
    def test_compressor(compressor: ImageCompressor, test_image: Image) -> CompressionResult:
        """Тестирование одного компрессора"""

        original_bytes = test_image.tobytes()
        original_size = len(original_bytes)

        # Сжатие
        start_time = time.time()
        compressed_data, metadata = compressor.compress(test_image)
        compression_time = time.time() - start_time

        compressed_size = len(compressed_data)

        # Декомпрессия
        start_time = time.time()
        _ = compressor.decompress(compressed_data, metadata['size'])
        decompression_time = time.time() - start_time

        # Расчет метрик
        compression_ratio = compressed_size / original_size

        result = CompressionResult(
            original_size=original_size,
            compressed_size=compressed_size,
            compression_time=compression_time,
            decompression_time=decompression_time,
            compression_ratio=compression_ratio,
            algorithm=str(type(compressor)),
            quantization_method=compressor.quantizer.__class__.__name__ if compressor.quantizer else None,
            original_dimensions=test_image.size
        )

        return result

    @staticmethod
    def compare_compressors(compressors: Dict[str, ImageCompressor], test_image: Image) -> List[CompressionResult]:
        """Сравнение нескольких компрессоров"""
        results = []
        for name, compressor in compressors.items():
            result = CompressorAnalyzer.test_compressor(compressor, test_image)
            results.append(result)
        results.sort(key=lambda x: x.compression_ratio)
        return results

    @staticmethod
    def print_results(results):
        """Генерация отчета по всем тестам в виде таблицы"""
        if not results:
            return "No test results available"

        report = ["Compression Analysis Report:", "=" * 50]

        # Форматированная шапка таблицы
        report.append(
            f"{'CompTime(s)':<10} {'DecompTime(s)':<10} {'Original(KB)':<10} {'Compressed(KB)':<10} {'Ratio':<8} {'Quantization':<12} {'Algorithm':<15}")
        report.append("-" * 85)

        # Данные таблицы
        for result in sorted(results, key=lambda x: x.compression_ratio):
            report.append(
                f"{result.compression_time:<10.4f} "
                f"{result.decompression_time:<10.4f} "
                f"{result.original_size // 1024:<10} "
                f"{result.compressed_size // 1024:<10} "
                f"{result.compression_ratio:<8.4f}"
                f"{(result.quantization_method or 'None'):<12} "
                f"{result.algorithm:<15} "
            )

        print("\n".join(report))


if __name__ == "__main__":
    input_image = Image.open(r"C:\Users\UserLog.ru\PycharmProjects\regular\basic\image\data\v2.png")
    result = CompressorAnalyzer.test_compressor(ImageCompressorLZMAGS4(), input_image)
    CompressorAnalyzer.print_results([result])
