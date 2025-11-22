from pathlib import Path
from basic.image.__all_tools import *
from basic.image.compression.test.CompressorBenchmark import CompressorBenchmark

all_img_names = ["a2.png", "a3.png", "a4.png", "a5.png", "a6.png", "a7.png", "a8.png", "a9.png", "a10.png",
                 "g1.png", "g2.png"]
for img_name in ["a9.png"]:
    benchmark = CompressorBenchmark(Path(__file__).parent.parent.parent / "data" / img_name)
    benchmark.print_line()
    benchmark.print_compress_time_comparison_table(
        ThreadCompressor([BZ2Compressor(), BZ2Compressor()]), BZ2Compressor())
    benchmark.print_compress_ratio_comparison_table(
        ThreadCompressor([BZ2Compressor(), BZ2Compressor()]), BZ2Compressor())
