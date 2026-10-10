#!/usr/bin/env python3
"""Turn your profile picture into ASCII art for the README.

    pip install pillow
    python image_to_ascii.py me.jpg --width 60 > face.txt

Paste the result inside the <pre> block on the left of README.md.
Tips: use a close-up, well-lit photo with a plain background.
Add --invert if your face looks like a negative (dark theme usually needs it).
"""
import argparse
from PIL import Image, ImageOps

RAMP = "@%#*+=-:. "  # dark -> light


def convert(path, width, invert, contrast):
    img = Image.open(path).convert("L")
    img = ImageOps.autocontrast(img, cutoff=contrast)
    # characters are ~2x taller than wide, so halve the height
    height = int(img.height / img.width * width * 0.5)
    img = img.resize((width, height))
    ramp = RAMP[::-1] if invert else RAMP
    px = img.load()
    rows = []
    for y in range(height):
        row = "".join(ramp[px[x, y] * (len(ramp) - 1) // 255] for x in range(width))
        rows.append(row.rstrip())
    return "\n".join(rows)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--width", type=int, default=60)
    ap.add_argument("--invert", action="store_true")
    ap.add_argument("--contrast", type=int, default=2)
    a = ap.parse_args()
    print(convert(a.image, a.width, a.invert, a.contrast))
