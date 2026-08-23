from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "title-dispersion-v1-source.png"
OUTPUT_DIR = ROOT / "assets" / "title-dispersion"

ROWS = {
    "intact": (0, 0, 1536, 341),
    "mid": (0, 341, 1536, 682),
    "late": (0, 682, 1536, 1023),
}


def remove_magenta(image: Image.Image) -> Image.Image:
    rgb = np.asarray(image.convert("RGB")).astype(np.float32)
    red, green, blue = np.moveaxis(rgb, 2, 0)

    # The matte is a flat #ff00ff. Green is therefore a reliable alpha signal
    # for the ivory title and its soft physical shadows.
    alpha = np.clip((green - 3.0) / 218.0, 0.0, 1.0)
    alpha = np.power(alpha, 0.84)

    safe_alpha = np.maximum(alpha, 1 / 255)
    foreground = np.empty_like(rgb)
    foreground[:, :, 0] = (red - 255.0 * (1.0 - alpha)) / safe_alpha
    foreground[:, :, 1] = green / safe_alpha
    foreground[:, :, 2] = (blue - 255.0 * (1.0 - alpha)) / safe_alpha
    foreground = np.clip(foreground, 0, 255).astype(np.uint8)

    # Neutralize chroma spill at semi-transparent cotton edges while keeping
    # the fully opaque cloud texture untouched.
    edge = alpha < 0.94
    value = foreground.max(axis=2)
    foreground[edge, 0] = value[edge]
    foreground[edge, 1] = (value[edge] * 0.98).astype(np.uint8)
    foreground[edge, 2] = (value[edge] * 0.94).astype(np.uint8)

    rgba = np.dstack([foreground, (alpha * 255).astype(np.uint8)])
    return Image.fromarray(rgba, "RGBA")


sheet = Image.open(SOURCE).convert("RGB")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

for name, box in ROWS.items():
    output = remove_magenta(sheet.crop(box))
    output.save(OUTPUT_DIR / f"title-{name}.png", optimize=True)
    alpha = output.getchannel("A")
    print(name, output.size, alpha.getbbox())
