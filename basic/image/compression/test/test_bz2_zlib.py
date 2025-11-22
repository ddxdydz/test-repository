from pathlib import Path
from basic.image.__all_tools import *
from basic.image.compression.test.CompressorBenchmark import CompressorBenchmark

for img_name in ["a2.png", "a3.png", "a4.png", "a5.png", "a6.png", "a7.png", "a8.png", "a9.png", "a10.png",
                 "g1.png", "g2.png"]:
    benchmark = CompressorBenchmark(Path(__file__).parent.parent.parent / "data" / img_name)
    benchmark.print_line()
    benchmark.print_compress_time_comparison_table(BZ2Compressor(), ZlibCompressor())
    benchmark.print_compress_ratio_comparison_table(BZ2Compressor(), ZlibCompressor())
