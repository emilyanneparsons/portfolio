from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "fog-banks-v1-source.png"
OUTPUT_DIR = ROOT / "assets" / "fog-banks"

# The ImageGen sheet is intentionally arranged as three isolated rows. The
# boxes stay generous so none of the paper edges or their soft shadows are
# clipped during extraction.
ROWS = {
    "thin": (0, 36, 1536, 276),
    "medium": (0, 286, 1536, 568),
    "dense": (0, 556, 1536, 1024),
}


def paper_mask(rgb: np.ndarray) -> Image.Image:
    red = rgb[:, :, 0].astype(np.int16)
    green = rgb[:, :, 1].astype(np.int16)
    blue = rgb[:, :, 2].astype(np.int16)

    # The generated paper is distinctly warm ivory, while the studio matte is
    # neutral charcoal/grey. This keeps the fibers and removes the matte.
    warmth = red - blue
    core = (red > 214) & (green > 204) & (blue > 188) & (warmth >= 10)

    mask = Image.fromarray(np.where(core, 255, 0).astype(np.uint8), "L")
    mask = mask.filter(ImageFilter.MaxFilter(5))
    mask = mask.filter(ImageFilter.MinFilter(3))
    mask = mask.filter(ImageFilter.GaussianBlur(0.9))
    return mask


image = Image.open(SOURCE).convert("RGB")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

for name, box in ROWS.items():
    crop = image.crop(box)
    rgb = np.asarray(crop)
    alpha = paper_mask(rgb)
    rgba = crop.convert("RGBA")
    rgba.putalpha(alpha)

    bbox = alpha.getbbox()
    if bbox is None:
        raise RuntimeError(f"No paper fog detected in {name} row")

    pad = 10
    left = max(0, bbox[0] - pad)
    top = max(0, bbox[1] - pad)
    right = min(rgba.width, bbox[2] + pad)
    bottom = min(rgba.height, bbox[3] + pad)
    output = rgba.crop((left, top, right, bottom))
    output.save(OUTPUT_DIR / f"fog-{name}.png", optimize=True)
    print(name, output.size, output.getchannel("A").getbbox())
