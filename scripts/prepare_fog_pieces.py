from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "fog-pieces-v1-source.png"
OUTPUT_DIR = ROOT / "assets" / "fog-pieces"

CELLS = [
    (0, 0, 768, 341),
    (768, 0, 1536, 341),
    (0, 341, 768, 683),
    (768, 341, 1536, 683),
    (0, 683, 768, 1024),
    (768, 683, 1536, 1024),
]


def remove_magenta(image: Image.Image) -> Image.Image:
    rgb = np.asarray(image.convert("RGB")).astype(np.float32)
    red, green, blue = np.moveaxis(rgb, 2, 0)
    alpha = np.clip((green - 3.0) / 218.0, 0.0, 1.0)
    alpha = np.power(alpha, 0.84)
    alpha[alpha < 0.08] = 0.0

    safe_alpha = np.maximum(alpha, 1 / 255)
    foreground = np.empty_like(rgb)
    foreground[:, :, 0] = (red - 255.0 * (1.0 - alpha)) / safe_alpha
    foreground[:, :, 1] = green / safe_alpha
    foreground[:, :, 2] = (blue - 255.0 * (1.0 - alpha)) / safe_alpha
    foreground = np.clip(foreground, 0, 255).astype(np.uint8)

    edge = alpha < 0.94
    value = foreground.max(axis=2)
    foreground[edge, 0] = value[edge]
    foreground[edge, 1] = (value[edge] * 0.98).astype(np.uint8)
    foreground[edge, 2] = (value[edge] * 0.94).astype(np.uint8)
    return Image.fromarray(
        np.dstack([foreground, (alpha * 255).astype(np.uint8)]),
        "RGBA",
    )


sheet = Image.open(SOURCE).convert("RGB")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

for index, box in enumerate(CELLS, start=1):
    piece = remove_magenta(sheet.crop(box))
    alpha = piece.getchannel("A")
    bbox = alpha.point(lambda value: 255 if value > 40 else 0).getbbox()
    if bbox is None:
        raise RuntimeError(f"No fog detected in cell {index}")

    pad = 8
    left = max(0, bbox[0] - pad)
    top = max(0, bbox[1] - pad)
    right = min(piece.width, bbox[2] + pad)
    bottom = min(piece.height, bbox[3])
    output = piece.crop((left, top, right, bottom))
    output.save(OUTPUT_DIR / f"fog-piece-{index}.png", optimize=True)
    print(index, output.size, output.getchannel("A").getbbox())
