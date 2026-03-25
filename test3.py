from basic.image.ToolsManager import ToolsManager


tools_manager = ToolsManager(768, 1024, 2, 100, "bin")
# tools_manager = ToolsManager(1920, 1080, 2, 100, "bin")
print(tools_manager)
stats, diff, encoded = tools_manager.encode_image()
tools_manager.print_encode_stats(stats)
stats, decoded = tools_manager.decode_image(encoded)
tools_manager.print_decode_stats(stats)
# tools_manager.show_decoded_image(decoded)
