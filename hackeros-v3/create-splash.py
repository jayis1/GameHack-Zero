#!/usr/bin/env python3
"""Generate an original, U-Boot-compatible 24-bit GameHack Zero splash."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "staging/boot-assets"
OUTPUT.mkdir(parents=True, exist_ok=True)
image = Image.new("RGB", (640, 480), (9, 12, 16))
draw = ImageDraw.Draw(image)
amber = (255, 165, 40)
light = (255, 234, 193)
dim = (80, 64, 42)

font_dir = next(path for path in (Path("/usr/share/fonts/TTF"), Path("/usr/share/fonts/truetype/dejavu"))
                if (path / "DejaVuSansMono-Bold.ttf").exists())
title = ImageFont.truetype(str(font_dir / "DejaVuSansMono-Bold.ttf"), 46)
subtitle = ImageFont.truetype(str(font_dir / "DejaVuSansMono.ttf"), 15)
small = ImageFont.truetype(str(font_dir / "DejaVuSansMono.ttf"), 12)

for y in range(0, 480, 24):
    draw.line((0, y, 639, y), fill=(15, 19, 23))
for x in range(0, 640, 24):
    draw.line((x, 0, x, 479), fill=(15, 19, 23))
draw.rounded_rectangle((22, 22, 617, 457), radius=18, outline=dim, width=2)
for side in (0, 1):
    for y in (100, 150, 205, 335, 380):
        x = 40 if not side else 600
        end = x + 72 if not side else x - 72
        draw.line((x, y, end, y, end, y + 18), fill=dim, width=2)
        draw.ellipse((end - 3, y + 15, end + 3, y + 21), outline=amber)

# Original pocket-console emblem with terminal glyph.
draw.rounded_rectangle((249, 65, 391, 204), radius=19, fill=(20, 24, 28), outline=amber, width=3)
draw.rounded_rectangle((264, 80, 376, 151), radius=7, fill=(7, 10, 13), outline=dim, width=2)
draw.line((287, 101, 303, 115, 287, 129), fill=amber, width=4)
draw.line((315, 129, 344, 129), fill=light, width=4)
draw.rectangle((270, 172, 296, 180), fill=amber)
draw.rectangle((279, 163, 287, 189), fill=amber)
draw.ellipse((346, 172, 357, 183), fill=amber)
draw.ellipse((366, 161, 377, 172), fill=light)

def centered(text, y, font, color):
    width = draw.textbbox((0, 0), text, font=font)[2]
    draw.text(((640 - width) // 2, y), text, font=font, fill=color)

centered("GAMEHACK", 225, title, light)
centered("Z E R O", 280, title, amber)
centered("POCKET LINUX // R36XX EDITION", 351, subtitle, light)
draw.line((155, 384, 485, 384), fill=dim, width=2)
draw.line((155, 384, 267, 384), fill=amber, width=3)
centered("WIFI  /  BLUETOOTH  /  INFRARED", 403, small, amber)
centered("4.2.0  -  INITIALIZING SYSTEM", 425, small, (155, 150, 139))
image.save(OUTPUT / "logo.bmp", format="BMP")
image.save(OUTPUT / "preview.png", format="PNG")
print(OUTPUT / "logo.bmp")
