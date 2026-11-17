"""Maakt 6 icoon-voorstellen in previews/iconen/ + overzicht previews/iconen.png"""
import math, os
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageFont

S = 512
OUT = "previews/iconen"
os.makedirs(OUT, exist_ok=True)
FONT = next((p for p in ["/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf", "/System/Library/Fonts/Helvetica.ttc"] if os.path.exists(p)), None)

def blank(): return Image.new("RGBA", (S, S), (0, 0, 0, 0))
def gmask(): return Image.new("L", (S, S), 0)

def mesh(base, blobs):
    img = Image.new("RGBA", (S, S), base + (255,))
    for (x, y, r, col) in blobs:
        l = blank(); ImageDraw.Draw(l).ellipse([x - r, y - r, x + r, y + r], fill=col + (255,))
        l = l.filter(ImageFilter.GaussianBlur(r * .55)); img = Image.alpha_composite(img, l)
    return img

def squircle(img, pad=22, rad=112):
    m = gmask(); ImageDraw.Draw(m).rounded_rectangle([pad, pad, S - pad, S - pad], radius=rad, fill=255)
    img = img.copy(); img.putalpha(m); return img

def smooth(mask, blur=14):
    m = mask.filter(ImageFilter.GaussianBlur(blur))
    return m.point(lambda v: 255 if v > 128 else 0).filter(ImageFilter.GaussianBlur(1.2))

def erode(m, k): return m.filter(ImageFilter.MinFilter(2 * k + 1))

def tint(mask, col, a=255):
    l = Image.new("RGBA", (S, S), col + (0,)); l.putalpha(mask.point(lambda v: v * a // 255)); return l

def glass(img, mask, fill=46, shadow=95, rim=215, shade=(20, 0, 70)):
    """Zet 'vloeibaar glas' op de vorm in mask."""
    sh = ImageChops.offset(mask, 0, 14).filter(ImageFilter.GaussianBlur(16))
    img = Image.alpha_composite(img, tint(sh, shade, shadow))
    img = Image.alpha_composite(img, tint(mask, (255, 255, 255), fill))
    inner = erode(mask, 9)
    ring = ImageChops.subtract(mask, inner).filter(ImageFilter.GaussianBlur(1.5))
    img = Image.alpha_composite(img, tint(ring, (255, 255, 255), rim))
    e2 = erode(mask, 20)
    hl = ImageChops.subtract(e2, ImageChops.offset(e2, 22, 30)).filter(ImageFilter.GaussianBlur(7))
    img = Image.alpha_composite(img, tint(hl, (255, 255, 255), 230))
    ca = ImageChops.subtract(e2, ImageChops.offset(e2, -20, -26)).filter(ImageFilter.GaussianBlur(9))
    img = Image.alpha_composite(img, tint(ca, (170, 235, 255), 150))
    return img

def font(sz): return ImageFont.truetype(FONT, sz) if FONT else ImageFont.load_default()

def arrow(img, cx, cy, w, col=(255, 255, 255), shade=True):
    m = gmask(); d = ImageDraw.Draw(m)
    t = w * .26
    d.rounded_rectangle([cx - t / 2, cy - w * .5, cx + t / 2, cy + w * .12], radius=t / 2, fill=255)
    d.polygon([(cx - w * .46, cy - w * .02), (cx + w * .46, cy - w * .02), (cx, cy + w * .5)], fill=255)
    d.rounded_rectangle([cx - w * .56, cy + w * .60, cx + w * .56, cy + w * .60 + t * .8], radius=t * .4, fill=255)
    m = m.filter(ImageFilter.GaussianBlur(3)).point(lambda v: 255 if v > 110 else v * 2)
    if shade: img = Image.alpha_composite(img, tint(ImageChops.offset(m, 0, 8).filter(ImageFilter.GaussianBlur(8)), (30, 0, 90), 110))
    return Image.alpha_composite(img, tint(m, col, 255))

# ---------- 1: glazen orb met vloeistof ----------
def v1():
    img = mesh((18, 8, 70), [(90, 110, 260, (255, 70, 150)), (440, 140, 250, (120, 80, 255)), (300, 470, 300, (0, 200, 255)), (80, 440, 180, (255, 170, 60))])
    cx, cy, r = 256, 262, 170
    m = gmask(); ImageDraw.Draw(m).ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    img = glass(img, m, fill=34)
    liq = blank(); ld = ImageDraw.Draw(liq)
    pts = [(x, cy + 30 + 16 * math.sin(x / 38)) for x in range(0, S + 1, 4)] + [(S, S), (0, S)]
    lm = gmask(); ImageDraw.Draw(lm).polygon(pts, fill=255)
    lm = ImageChops.multiply(lm, erode(m, 8)).filter(ImageFilter.GaussianBlur(1))
    grad = Image.new("RGBA", (S, S)); gd = ImageDraw.Draw(grad)
    for y in range(S): gd.line([(0, y), (S, y)], fill=(int(255 - y * .2), int(120 + y * .25), 255, 255))
    grad.putalpha(lm.point(lambda v: v * 210 // 255)); img = Image.alpha_composite(img, grad)
    surf = ImageChops.subtract(lm, ImageChops.offset(lm, 0, 6)).filter(ImageFilter.GaussianBlur(2)); img = Image.alpha_composite(img, tint(surf, (255, 255, 255), 255))
    for (bx, by, br) in [(215, 330, 13), (292, 360, 9), (262, 300, 7)]:
        bm = gmask(); ImageDraw.Draw(bm).ellipse([bx - br, by - br, bx + br, by + br], fill=255)
        img = Image.alpha_composite(img, tint(ImageChops.subtract(bm, erode(bm, 3)), (255, 255, 255), 230))
    return squircle(img)

# ---------- 2: download-pijl in glazen tegel ----------
def v2():
    img = mesh((12, 20, 90), [(60, 80, 280, (0, 190, 255)), (460, 100, 250, (150, 90, 255)), (380, 470, 280, (255, 90, 180)), (60, 460, 200, (80, 255, 210))])
    m = gmask(); ImageDraw.Draw(m).rounded_rectangle([96, 96, 416, 416], radius=96, fill=255)
    img = glass(img, m, fill=52)
    img = arrow(img, 256, 230, 150)
    return squircle(img)

# ---------- 3: druppel met pijl ----------
def v3():
    img = mesh((38, 6, 56), [(256, 60, 300, (255, 110, 60)), (80, 420, 260, (255, 40, 120)), (450, 420, 240, (150, 60, 255))])
    m = gmask(); d = ImageDraw.Draw(m)
    d.ellipse([256 - 138, 300 - 138, 256 + 138, 300 + 138], fill=255)
    d.polygon([(256, 62), (256 - 128, 250), (256 + 128, 250)], fill=255)
    m = smooth(m, 18)
    img = glass(img, m, fill=44)
    img = arrow(img, 256, 290, 110)
    return squircle(img)

# ---------- 4: B-monogram ----------
def v4():
    img = mesh((24, 10, 80), [(70, 90, 280, (255, 160, 60)), (450, 90, 250, (255, 60, 140)), (260, 470, 300, (110, 70, 255)), (440, 400, 160, (0, 210, 255))])
    m = gmask(); d = ImageDraw.Draw(m); f = font(400)
    bb = d.textbbox((0, 0), "B", font=f); w, h = bb[2] - bb[0], bb[3] - bb[1]
    d.text((256 - w / 2 - bb[0], 262 - h / 2 - bb[1]), "B", font=f, fill=255)
    m = smooth(m.filter(ImageFilter.MaxFilter(5)), 4)
    img = glass(img, m, fill=70, rim=235)
    return squircle(img)

# ---------- 5: twee samensmeltende bellen ----------
def v5():
    img = mesh((10, 6, 48), [(140, 150, 260, (120, 70, 255)), (420, 400, 280, (0, 190, 255)), (400, 90, 200, (255, 70, 170)), (70, 450, 190, (255, 160, 70))])
    m = gmask(); d = ImageDraw.Draw(m)
    d.ellipse([88, 150, 88 + 230, 150 + 230], fill=255)
    d.ellipse([268, 120, 268 + 150, 120 + 150], fill=255)
    d.polygon([(250, 255), (300, 200), (330, 240), (270, 320)], fill=255)
    m = smooth(m, 20)
    img = glass(img, m, fill=40)
    m2 = gmask(); ImageDraw.Draw(m2).ellipse([330, 330, 330 + 74, 330 + 74], fill=255)
    img = glass(img, smooth(m2, 4), fill=40, shadow=70)
    return squircle(img)

# ---------- 6: voortgangsring ----------
def v6():
    img = mesh((8, 6, 34), [(256, 256, 250, (50, 20, 130)), (110, 400, 200, (255, 60, 160)), (420, 120, 200, (0, 200, 255))])
    ring = gmask(); d = ImageDraw.Draw(ring)
    box = [256 - 168, 256 - 168, 256 + 168, 256 + 168]
    d.arc(box, -90, 190, fill=255, width=46)
    for ang in (-90, 190):
        x = 256 + 168 * math.cos(math.radians(ang)) - 0; y = 256 + 168 * math.sin(math.radians(ang))
    # afgeronde uiteinden
    for ang in (-90, 190):
        x = 256 + 145 * math.cos(math.radians(ang)); y = 256 + 145 * math.sin(math.radians(ang))
        d.ellipse([x - 23, y - 23, x + 23, y + 23], fill=255)
    base = gmask(); ImageDraw.Draw(base).ellipse(box, outline=255, width=46)
    img = Image.alpha_composite(img, tint(base, (255, 255, 255), 28))
    grad = Image.new("RGBA", (S, S)); gd = ImageDraw.Draw(grad)
    for y in range(S):
        t = y / S
        gd.line([(0, y), (S, y)], fill=(int(0 + 255 * t), int(220 - 130 * t), int(255 - 60 * t), 255))
    grad.putalpha(ring); glow = grad.filter(ImageFilter.GaussianBlur(14))
    img = Image.alpha_composite(img, glow); img = Image.alpha_composite(img, grad)
    img = Image.alpha_composite(img, tint(ImageChops.subtract(ring, erode(ring, 5)).filter(ImageFilter.GaussianBlur(1)), (255, 255, 255), 190))
    img = arrow(img, 256, 248, 96)
    return squircle(img)

if __name__ == "__main__":
    variants = [("1 Glazen orb", v1), ("2 Pijl in glas", v2), ("3 Druppel", v3), ("4 B-monogram", v4), ("5 Bellen", v5), ("6 Voortgangsring", v6)]
    cell = 360; pad = 28
    sheet = Image.new("RGBA", (3 * cell + 4 * pad, 2 * (cell + 44) + 3 * pad), (22, 20, 36, 255))
    for i, (name, fn) in enumerate(variants):
        im = fn(); im.save("%s/%s.png" % (OUT, name.replace(" ", "-")))
        t = im.resize((cell, cell), Image.LANCZOS)
        x = pad + (i % 3) * (cell + pad); y = pad + (i // 3) * (cell + 44 + pad)
        sheet.alpha_composite(t, (x, y))
        ImageDraw.Draw(sheet).text((x + 6, y + cell + 10), name, font=font(24), fill=(255, 255, 255, 255))
    sheet.save("previews/iconen.png")
    print("klaar")
