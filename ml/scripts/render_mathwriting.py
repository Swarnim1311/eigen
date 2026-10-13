"""Render MathWriting InkML strokes to grayscale PNGs for PosFormer inference.

Input : ml/data/mathwriting-2024-excerpt/{split}/*.inkml  (CC BY-NC-SA 4.0, eval use)
Output: ml/data/renders/<split>/<sample_id>_<w|b>.png
        _w = black ink on white paper ; _b = white ink on black (CROHME-style?).
        Polarity is CALIBRATED empirically in run_posformer.py (see report);
        both are rendered so the choice is documented, not assumed.

Rendering: 1 unit = 1 px, global offset removed, PAD-px margin, PIL line width
STROKE_W. No blur/noise augmentation (Phase-1 baseline must be clean renders).
"""
import os
import sys
import xml.etree.ElementTree as ET

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))          # eigen/
DATA = os.path.join(REPO, "ml", "data")
SRC = os.path.join(DATA, "mathwriting-2024-excerpt")
OUT = os.path.join(DATA, "renders")

NS = {"ink": "http://www.w3.org/2003/InkML"}
STROKE_W = 4
PAD = 12


def parse_inkml(path):
    root = ET.parse(path).getroot()
    label = None
    for ann in root.findall("ink:annotation", NS):
        if ann.get("type") == "normalizedLabel":
            label = (ann.text or "").strip()
    strokes = []
    for trace in root.findall("ink:trace", NS):
        pts = []
        for tok in (trace.text or "").strip().replace(",", " ").split():
            pass
        # traces are "x y t,x y t,..." — split on comma first
        for grp in (trace.text or "").strip().split(","):
            nums = grp.strip().split()
            if len(nums) >= 2:
                pts.append((float(nums[0]), float(nums[1])))
        if pts:
            strokes.append(pts)
    return label, strokes


def render(strokes, ink, paper):
    xs = [x for s in strokes for x, _ in s]
    ys = [y for s in strokes for _, y in s]
    minx, miny, maxx, maxy = min(xs), min(ys), max(xs), max(ys)
    W = int(round(maxx - minx)) + 2 * PAD + 1
    H = int(round(maxy - miny)) + 2 * PAD + 1
    img = Image.new("L", (W, H), paper)
    d = ImageDraw.Draw(img)
    for s in strokes:
        pts = [(x - minx + PAD, y - miny + PAD) for x, y in s]
        if len(pts) == 1:
            x, y = pts[0]
            d.ellipse([x - STROKE_W / 2, y - STROKE_W / 2,
                       x + STROKE_W / 2, y + STROKE_W / 2], fill=ink)
        else:
            d.line(pts, fill=ink, width=STROKE_W, joint="curve")
    return img


def main():
    splits = sys.argv[1:] or ["test"]
    n = 0
    for split in splits:
        srcdir = os.path.join(SRC, split)
        outdir = os.path.join(OUT, split)
        os.makedirs(outdir, exist_ok=True)
        manifest = []
        for fn in sorted(os.listdir(srcdir)):
            if not fn.endswith(".inkml"):
                continue
            sid = fn[:-len(".inkml")]
            label, strokes = parse_inkml(os.path.join(srcdir, fn))
            if not strokes or label is None:
                print(f"SKIP {split}/{sid}: no strokes/label")
                continue
            render(strokes, ink=0, paper=255).save(os.path.join(outdir, f"{sid}_w.png"))
            render(strokes, ink=255, paper=0).save(os.path.join(outdir, f"{sid}_b.png"))
            manifest.append(f"{sid}\t{label}")
            n += 1
        with open(os.path.join(outdir, "labels.tsv"), "w", encoding="utf-8") as f:
            f.write("\n".join(manifest) + "\n")
    print(f"rendered {n} samples (both polarities) -> {OUT}")


if __name__ == "__main__":
    main()
