from pathlib import Path
from basic.image.__all_tools import *
from basic.image.compression.test.CompressorBenchmark import CompressorBenchmark

for img_name in ["a2.jpg", "a3.jpg", "a4.jpg", "a5.jpg", "a6.jpg", "a7.jpg", "a8.jpg", "a9.jpg", "a10.jpg",
                 "g1.jpg", "g2.jpg"]:
    benchmark = CompressorBenchmark(Path(__file__).parent.parent.parent / "data" / img_name)
    benchmark.print_line()
    benchmark.print_compress_time_comparison_table(BZ2Compressor(), ZlibCompressor())
    benchmark.print_compress_ratio_comparison_table(BZ2Compressor(), ZlibCompressor())
