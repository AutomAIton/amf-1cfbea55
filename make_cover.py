"""Writes docs/cover.png (1400x1400, the size Apple Podcasts wants). Run once; the PNG is committed."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SIZE = 1400
BG, FG, ACCENT = (12, 18, 32), (240, 244, 248), (56, 189, 248)
FONTS = ["C:/Windows/Fonts/segoeuib.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]


def font(size):
    for path in FONTS:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


img = Image.new("RGB", (SIZE, SIZE), BG)
d = ImageDraw.Draw(img)


def centered(text, y, f, fill):
    d.text(((SIZE - d.textlength(text, font=f)) / 2, y), text, font=f, fill=fill)


centered("AI", 300, font(440), FG)
centered("MORNING", 790, font(170), FG)
d.rectangle([(400, 1010), (SIZE - 400, 1024)], fill=ACCENT)
centered("models · agents · security", 1080, font(64), ACCENT)

out = Path(__file__).parent / "docs" / "cover.png"
out.parent.mkdir(exist_ok=True)
img.save(out)
print("wrote", out)
