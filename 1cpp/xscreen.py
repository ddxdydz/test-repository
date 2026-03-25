from PIL import Image
import Xlib.display
from time import time

dsp = Xlib.display.Display()
root = dsp.screen().root

s = time()
raw = root.get_image(0, 0, 1024, 768, Xlib.X.ZPixmap, 0xffffffff)
image = Image.frombytes("RGB", (1024, 768), raw.data, "raw", "BGRX")
image.save('./xscreen.png')
print(time() - s)
