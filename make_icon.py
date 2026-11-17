"""Tekent het app-icoon (glazen orb op kleurverloop) en maakt icon.icns + icon.ico. Gebruik: python3 make_icon.py"""
import os, subprocess, shutil
from PIL import Image, ImageDraw, ImageFilter, ImageChops

S = 1024
def lerp(a, b, t): return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

bg = Image.new("RGB", (S, S))
d = ImageDraw.Draw(bg)
stops = [(0.0, (255, 80, 150)), (0.5, (110, 70, 255)), (1.0, (0, 200, 255))]
for y in range(S):
    for x in range(0, S, 4):
        t = (x * .45 + y * .55) / S
        for i in range(len(stops) - 1):
            if stops[i][0] <= t <= stops[i + 1][0]:
                c = lerp(stops[i][1], stops[i + 1][1], (t - stops[i][0]) / (stops[i + 1][0] - stops[i][0]))
        d.line([(x, y), (x + 3, y)], fill=c)
bg = bg.filter(ImageFilter.GaussianBlur(2)).convert("RGBA")

# glazen orb
orb = Image.new("RGBA", (S, S), (0, 0, 0, 0))
od = ImageDraw.Draw(orb)
cx, cy, r = S // 2, S // 2 + 10, 300
od.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255, 60), outline=(255, 255, 255, 230), width=10)
# vloeistof onderin
liq = Image.new("RGBA", (S, S), (0, 0, 0, 0))
ld = ImageDraw.Draw(liq)
ld.rectangle([0, cy + 40, S, S], fill=(255, 255, 255, 120))
mask = Image.new("L", (S, S), 0)
ImageDraw.Draw(mask).ellipse([cx - r + 10, cy - r + 10, cx + r - 10, cy + r - 10], fill=255)
liq.putalpha(ImageChops.multiply(liq.split()[3], mask))
# glans
gl = Image.new("RGBA", (S, S), (0, 0, 0, 0))
ImageDraw.Draw(gl).ellipse([cx - 190, cy - 230, cx - 40, cy - 110], fill=(255, 255, 255, 190))
gl = gl.filter(ImageFilter.GaussianBlur(14))
shadow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
ImageDraw.Draw(shadow).ellipse([cx - r, cy - r + 40, cx + r, cy + r + 40], fill=(20, 0, 80, 120))
shadow = shadow.filter(ImageFilter.GaussianBlur(40))
img = Image.alpha_composite(bg, shadow)
img = Image.alpha_composite(img, orb)
img = Image.alpha_composite(img, liq)
img = Image.alpha_composite(img, gl)

# afgeronde hoeken (macOS-stijl)
m = Image.new("L", (S, S), 0)
ImageDraw.Draw(m).rounded_rectangle([40, 40, S - 40, S - 40], radius=225, fill=255)
img.putalpha(m)
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
