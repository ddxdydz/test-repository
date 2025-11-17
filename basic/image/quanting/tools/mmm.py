import numpy as np
from PIL import Image
from time import time

img1 = np.array(Image.open(r"C:\Users\UserLog.ru\PycharmProjects\regular\basic\image\data\v4.png"), dtype=np.uint8)
img2 = np.array(Image.open(r"C:\Users\UserLog.ru\PycharmProjects\regular\basic\image\data\v4.png"), dtype=np.uint8)

s = time()
res = img2 - img1
print(time() - s)
print(res)