"""Convert the generated fog artwork's baked checkerboard to real transparency."""

from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "fog-engulf-v2.png"
OUTPUT = ROOT / "assets" / "fog-engulf-v2-clean.png"
TALL_OUTPUT = ROOT / "assets" / "fog-engulf-v2-clean-tall.png"
FILL_OUTPUT = ROOT / "assets" / "fog-paper-fill.png"
PIECE_SOURCE = ROOT / "assets" / "fog-pieces" / "fog-piece-1.png"
PIECE_TALL_OUTPUT = ROOT / "assets" / "fog-pieces" / "fog-piece-1-tall.png"


def main() -> None:
    image = Image.open(SOURCE).convert("RGB")
    pixels = np.asarray(image)
    height, width, _ = pixels.shape

    # The generated image contains a neutral pale checkerboard. The fog is
    # distinctly warmer, so only flood-fill near-neutral bright pixels that
    # are connected to the top edge. This preserves the fog's paper texture,
    # shadows, and antialiased contour while removing the synthetic backdrop.
    channel_range = pixels.max(axis=2).astype(np.int16) - pixels.min(axis=2).astype(np.int16)
    luminance = pixels.mean(axis=2)
    warm_delta = pixels[:, :, 0].astype(np.int16) - pixels[:, :, 2].astype(np.int16)
    removable = (channel_range <= 5) & (luminance >= 236) & (warm_delta <= 4)

    background = np.zeros((height, width), dtype=bool)
    queue: deque[tuple[int, int]] = deque()

    for x in range(width):
        if removable[0, x]:
            background[0, x] = True
            queue.append((0, x))

    while queue:
        y, x = queue.popleft()
        for next_y, next_x in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
            if (
                0 <= next_y < height
                and 0 <= next_x < width
                and removable[next_y, next_x]
                and not background[next_y, next_x]
            ):
                background[next_y, next_x] = True
                queue.append((next_y, next_x))

    foreground = (~background).astype(np.uint8) * 255
    alpha = Image.fromarray(foreground, mode="L").filter(ImageFilter.GaussianBlur(0.65))

    result = image.convert("RGBA")
    result.putalpha(alpha)
    result.save(OUTPUT, optimize=True)

    # Extend the opaque lower paper field with a mirrored section of its own
    # texture. Keeping this inside the bitmap avoids a visible CSS-color seam
    # while the fog is moving through and beyond the viewport.
    source_array = np.asarray(result)
    target_height = 1834
    tall_array = np.empty((target_height, width, 4), dtype=np.uint8)
    tall_array[:height] = source_array
    texture = source_array[-180:].copy()
    cursor = height
    flip = True
    while cursor < target_height:
        strip = texture[::-1] if flip else texture
        count = min(strip.shape[0], target_height - cursor)
        tall_array[cursor : cursor + count] = strip[:count]
        cursor += count
        flip = not flip

    tall_result = Image.fromarray(tall_array, mode="RGBA")
    tall_result.save(TALL_OUTPUT, optimize=True)

    # A separate texture field extends the rolled-in modular bank below the
    # viewport. It uses only the quiet bottom-most paper texture, avoiding the
    # decorative marks that appeared higher in the generated source.
    fill_height = 1080
    fill_array = np.empty((fill_height, width, 4), dtype=np.uint8)
    fill_texture = source_array[-120:].copy()
    cursor = 0
    flip = False
    while cursor < fill_height:
        strip = fill_texture[::-1] if flip else fill_texture
        count = min(strip.shape[0], fill_height - cursor)
        fill_array[cursor : cursor + count] = strip[:count]
        cursor += count
        flip = not flip

    fill_result = Image.fromarray(fill_array, mode="RGBA")
    fill_result.save(FILL_OUTPUT, optimize=True)

    # Build a genuinely tall modular fog piece rather than attaching a
    # rectangular CSS tail. Its original scalloped silhouette stays intact,
    # while the paper texture continues below the viewport as part of the
    # bitmap itself.
    piece = Image.open(PIECE_SOURCE).convert("RGBA")
    piece_width, piece_height = piece.size
    piece_tall_height = 900
    piece_tall = Image.new("RGBA", (piece_width, piece_tall_height), (0, 0, 0, 0))
    piece_fill = fill_result.resize((piece_width, piece_tall_height - piece_height + 1))
    fill_mask = Image.new("L", piece_fill.size, 0)
    fill_mask.paste(255, (8, 0, piece_width - 8, piece_fill.height))
    piece_tall.paste(piece_fill, (0, piece_height - 1), fill_mask)
    piece_tall.alpha_composite(piece, (0, 0))
    piece_tall.save(PIECE_TALL_OUTPUT, optimize=True)

    print(f"saved {OUTPUT}")
    print(f"mode={result.mode} size={result.size} alpha={alpha.getextrema()} bbox={alpha.getbbox()}")
    print(f"saved {TALL_OUTPUT} size={tall_result.size}")
    print(f"saved {FILL_OUTPUT} size={fill_result.size}")
    print(f"saved {PIECE_TALL_OUTPUT} size={piece_tall.size}")


if __name__ == "__main__":
    main()
