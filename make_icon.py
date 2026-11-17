"""Maakt icon.png, icon.icns en icon.ico uit het gekozen ontwerp (nummer 5, Bellen). Gebruik: python3 make_icon.py"""
import os, shutil, subprocess
from PIL import Image
import make_icon_options as o

img = o.v5().resize((1024, 1024), Image.LANCZOS)
img.save("icon.png")
os.makedirs("icon.iconset", exist_ok=True)
for sz in (16, 32, 64, 128, 256, 512, 1024):
    img.resize((sz, sz), Image.LANCZOS).save("icon.iconset/icon_%dx%d.png" % (sz, sz))
    if sz <= 512:
        img.resize((sz * 2, sz * 2), Image.LANCZOS).save("icon.iconset/icon_%dx%d@2x.png" % (sz, sz))
img.save("icon.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
try:
    subprocess.run(["iconutil", "-c", "icns", "icon.iconset", "-o", "icon.icns"], check=True)
except Exception as e:
    print("iconutil niet beschikbaar (alleen op Mac nodig):", e)
shutil.rmtree("icon.iconset", ignore_errors=True)
print("icoon klaar")
