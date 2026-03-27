from PIL import Image
import Xlib.display
import numpy as np
from time import time

dsp = Xlib.display.Display()
root = dsp.screen().root

s = time()
raw = root.get_image(0, 0, 1024, 768, Xlib.X.ZPixmap, 0xffffffff)
print("get_image", time() - s)

s = time()
data = np.asarray(raw, dtype=np.uint8)
print("asarray", time() - s, len(data.shape))

image = Image.frombytes("RGB", (1024, 768), raw.data, "raw", "BGRX")
image.save('./xscreen.png')

