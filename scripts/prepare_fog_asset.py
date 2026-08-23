from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "fog-engulf-v1-source.png"
OUTPUT = ROOT / "assets" / "fog-engulf-v1.png"


rgb = np.asarray(Image.open(SOURCE).convert("RGB"))
height, width = rgb.shape[:2]
high = rgb.max(axis=2).astype(np.int16)
low = rgb.min(axis=2).astype(np.int16)
chroma = high - low

# ImageGen rendered its transparency preview as pale neutral checkerboard
# pixels. The real paper fog is warmer, with visibly more red than blue. Flood
# only from the top edge so the white paper highlights inside the fog remain
# enclosed by their warmer paper edges.
background_candidate = (chroma <= 4) & (low > 235)
background = np.zeros((height, width), dtype=bool)
queue: deque[tuple[int, int]] = deque()


def add_background(y: int, x: int) -> None:
    if (
        0 <= y < height
        and 0 <= x < width
        and background_candidate[y, x]
        and not background[y, x]
    ):
        background[y, x] = True
        queue.append((y, x))


for x in range(width):
    add_background(0, x)

while queue:
    y, x = queue.popleft()
    add_background(y, x - 1)
    add_background(y, x + 1)
    add_background(y - 1, x)
    add_background(y + 1, x)

# Keep only the non-background component connected to the solid paper base.
# This removes any isolated compression speckles left in the transparent sky.
foreground_candidate = ~background
foreground = np.zeros((height, width), dtype=bool)
queue.clear()


def add_foreground(y: int, x: int) -> None:
    if (
        0 <= y < height
        and 0 <= x < width
        and foreground_candidate[y, x]
        and not foreground[y, x]
    ):
        foreground[y, x] = True
        queue.append((y, x))


for x in range(width):
    add_foreground(height - 1, x)

while queue:
    y, x = queue.popleft()
    add_foreground(y, x - 1)
    add_foreground(y, x + 1)
    add_foreground(y - 1, x)
    add_foreground(y + 1, x)

alpha = np.where(foreground, 255, 0).astype(np.uint8)
alpha_image = Image.fromarray(alpha, "L").filter(ImageFilter.GaussianBlur(radius=0.6))
rgba = np.dstack([rgb, np.asarray(alpha_image)])
Image.fromarray(rgba, "RGBA").save(OUTPUT, optimize=True)

print(
    {
        "source": str(SOURCE),
        "output": str(OUTPUT),
        "canvas": [width, height],
        "transparent_pixels": int((rgba[:, :, 3] == 0).sum()),
        "opaque_pixels": int((rgba[:, :, 3] == 255).sum()),
        "partial_alpha_pixels": int(
            ((rgba[:, :, 3] > 0) & (rgba[:, :, 3] < 255)).sum()
        ),
    }
)
