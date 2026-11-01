"""Photo beside its photo-matched render, for the four fitted views (3d/renders/compare/), composed from the original
photos and the current renders (no older raster is reused).

Layout (as the 3 Oct sheets): the photo and the render each scaled to the sheet height, a 10 px white gap between
them, yellow labels bottom-left of each panel ("PHOTO <n>", "MODEL", Arial Bold 33 px). JPEG quality 88.

    <python with Pillow> 3d/tools/make_compare.py [--out DIR]          (default: 3d/renders/compare/)
"""
import argparse
import os

from PIL import Image, ImageDraw, ImageFont, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))                      # .../car-console
RENDERS = os.path.join(ROOT, "3d", "renders")
FONT = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
GAP, LABEL_PX, YELLOW = 10, 33, (255, 255, 0)

SHEETS = [  # (output, photo, render, sheet height)
    ("photo3483_vs_in_car_3483.jpg", "measurement-photos/IMG_3483.jpg", "in_car_3483.png", 900),
    ("photo3487_vs_table_side_3487.jpg", "measurement-photos/IMG_3487.jpg", "table_side_3487.png", 700),
    ("photo3491_vs_table_top_3491.jpg", "measurement-photos/IMG_3491.jpg", "table_top_3491.png", 700),
    ("photo3502_vs_underside.jpg", "measurement-photos/IMG_3502.jpg", "underside.png", 700),
]


def to_height(im, h):
    return im.resize((int(im.width * h / im.height), h), Image.LANCZOS)


def sheet(photo_path, render_path, h):
    ph = to_height(ImageOps.exif_transpose(Image.open(photo_path)).convert("RGB"), h)
    rd = to_height(Image.open(render_path).convert("RGB"), h)
    out = Image.new("RGB", (ph.width + GAP + rd.width, h), (255, 255, 255))
    out.paste(ph, (0, 0))
    out.paste(rd, (ph.width + GAP, 0))
    d = ImageDraw.Draw(out)
    f = ImageFont.truetype(FONT, LABEL_PX)
    n = os.path.basename(photo_path).split("_")[1].split(".")[0]
    d.text((12, h - 50), f"PHOTO {n}", font=f, fill=YELLOW)
    d.text((ph.width + GAP + 12, h - 50), "MODEL", font=f, fill=YELLOW)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=os.path.join(RENDERS, "compare"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    for name, photo, render, h in SHEETS:
        im = sheet(os.path.join(ROOT, photo), os.path.join(RENDERS, render), h)
        im.save(os.path.join(a.out, name), quality=88)
        print(f"[compare] {name}: {im.width}x{im.height}")


if __name__ == "__main__":
    main()
