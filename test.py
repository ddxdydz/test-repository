from pathlib import Path

from basic.image.ToolsManager import ToolsManager


if __name__ == "__main__":
    height, width = 768, 1024  # a0.png
    # height, width = 800, 1280  # a1.bmp
    # height, width = 720, 1280
    # height, width = 719, 1279
    # height, width = 264, 741  # a5
    # height, width = 480, 640  # a6
    # height, width = 524, 1890  # a9
    # height, width = 562, 920  # a8
    # height, width = 961, 1365  # a1

    tools_manager = ToolsManager(width, height, 2, 100, "bin")
    print(tools_manager)
    for image_name in ["a0.png"]:
    # for image_name in ["ch1.jpg", "ch2.jpg", "ch3.jpg", "ch3.jpg"]:
        tools_manager.print_divided_line()
        stats, diff, encoded = tools_manager.encode_image(
            Path(__file__).parent / "basic" / "image" / "data" / image_name
        )
        tools_manager.print_encode_stats(stats)

        stats, decoded = tools_manager.decode_image(encoded)
        tools_manager.print_decode_stats(stats)
    tools_manager.show_decoded_image(decoded)
