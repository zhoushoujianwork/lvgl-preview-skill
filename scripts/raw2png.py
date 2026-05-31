#!/usr/bin/env python3
# BGRA 原始帧 → PNG。 跑: python3 raw2png.py <in.raw> <out.png>
import sys
import struct
from PIL import Image

src, dst = sys.argv[1], sys.argv[2]
with open(src, "rb") as f:
    w, h = struct.unpack("<II", f.read(8))
    data = f.read()
# LVGL 32-bit color 在小端机上是 BGRA; PIL raw decoder 'BGRA' 处理通道顺序
img = Image.frombytes("RGBA", (w, h), data, "raw", "BGRA").convert("RGB")
img.save(dst)
print("wrote {} ({}x{})".format(dst, w, h))
