from PIL import Image, ImageFilter, ImageChops
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROOT, "assets")
src = Image.open(os.path.join(A, "envelope-src.jpg")).convert("RGB")

BODY_BOX = (29, 227, 547, 512)
OPEN_FLAP_BOX = (29, 9, 547, 228)
CLOSED_BOX = (20, 550, 554, 880)


def key_checker(img):
    """Remove the baked-in grey/white checkerboard by keying on 'redness'."""
    img = img.convert("RGBA")
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, _ = px[x, y]
            red = r - (g + b) / 2
            a = max(0, min(255, int((red - 10) * 9)))
            if a < 255:
                # decontaminate edge colour from the white background
                px[x, y] = (95, 14, 26, a)
    return img


body = key_checker(src.crop(BODY_BOX))
body.save(os.path.join(A, "env-body.png"))

open_flap = key_checker(src.crop(OPEN_FLAP_BOX))
open_flap.save(os.path.join(A, "env-flap-open.png"))

# Closed flap: find lace band lower contour via edge density.
closed = src.crop(CLOSED_BOX)
edges = closed.convert("L").filter(ImageFilter.FIND_EDGES).filter(ImageFilter.BoxBlur(4))
ep = edges.load()
W, H = closed.size
mask = Image.new("L", (W, H), 0)
mp = mask.load()
for x in range(W):
    y = 8
    while y < H and ep[x, y] <= 6:
        y += 1
    while y < H and ep[x, y] > 6:
        y += 1
    bottom = min(H, y)
    for yy in range(bottom):
        mp[x, yy] = 255
from PIL import ImageDraw
limit = Image.new("L", (W, H), 0)
ImageDraw.Draw(limit).polygon([(0, 0), (W, 0), (W, 84), (W // 2, 270), (0, 84)], fill=255)
mask = ImageChops.multiply(mask, limit)
mask = mask.filter(ImageFilter.MinFilter(5)).filter(ImageFilter.GaussianBlur(1.2))
bbox = mask.getbbox()
flap = closed.convert("RGBA")
flap.putalpha(mask)
flap = flap.crop((0, 0, W, bbox[3]))
scale = BODY_BOX[2] - BODY_BOX[0]
flap = flap.resize((scale, round(flap.height * scale / W)), Image.LANCZOS)
flap.save(os.path.join(A, "env-flap-closed.png"))

# Preview composite (closed state)
prev = Image.new("RGBA", (body.width, body.height + open_flap.height), (40, 4, 10, 255))
prev.alpha_composite(body, (0, open_flap.height))
prev.alpha_composite(flap, (0, open_flap.height))
prev.save(os.path.join(os.environ.get("TEMP", "."), "env-preview.png"))
print(body.size, open_flap.size, flap.size)
