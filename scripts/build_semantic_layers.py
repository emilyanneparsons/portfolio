from pathlib import Path
from collections import deque

import numpy as np
from PIL import Image, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
OUT = ASSETS / "layers" / "semantic-v1"
OUT.mkdir(parents=True, exist_ok=True)

ORIGINAL = Image.open(ASSETS / "homepage-background-desktop-v4-clean.png").convert("RGBA")
ENVIRONMENT = Image.open(ASSETS / "layers" / "environment-plate-v2.png").convert("RGBA").resize(ORIGINAL.size)
CLEAN_SKY = Image.open(ASSETS / "homepage-sky-texture-v1.webp").convert("RGBA").resize(ORIGINAL.size)
WIDTH, HEIGHT = ORIGINAL.size


def alpha_from(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGBA"))[:, :, 3]


def connected_sky(rgb: np.ndarray) -> np.ndarray:
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    candidate = (b > 145) & (g > 112) & (r < 165) & (b - r > 48) & (g - r > 24)
    sky = np.zeros((HEIGHT, WIDTH), dtype=bool)
    queue = deque()

    def add(y: int, x: int) -> None:
        if 0 <= y < HEIGHT and 0 <= x < WIDTH and candidate[y, x] and not sky[y, x]:
            sky[y, x] = True
            queue.append((y, x))

    for x in range(WIDTH):
        add(0, x)
        add(HEIGHT - 1, x)
    for y in range(HEIGHT):
        add(y, 0)
        add(y, WIDTH - 1)

    while queue:
        y, x = queue.popleft()
        add(y, x - 1)
        add(y, x + 1)
        add(y - 1, x)
        add(y + 1, x)
    return sky


def save_source_layer(name: str, mask: np.ndarray) -> None:
    rgba = np.asarray(ORIGINAL).copy()
    rgba[:, :, 3] = np.where(mask, 255, 0).astype(np.uint8)
    rgba[~mask, :3] = 0
    Image.fromarray(rgba, "RGBA").save(OUT / f"{name}.png", optimize=True)


original = np.asarray(ORIGINAL)
sky = connected_sky(original[:, :, :3])
objects = ~sky

foreground_alpha = alpha_from(ASSETS / "homepage-foreground-bushes.png")
cloud_paths = [
    ASSETS / "scroll-layers" / "cloud-left-top.webp",
    ASSETS / "scroll-layers" / "cloud-right-top.webp",
    ASSETS / "scroll-layers" / "cloud-left-low.webp",
    ASSETS / "scroll-layers" / "cloud-right-low.webp",
]
cloud_source_alphas = [alpha_from(path) for path in cloud_paths]
cloud_masks = [alpha > 16 for alpha in cloud_source_alphas]
cloud_clear_masks = [
    np.asarray(
        Image.fromarray(np.where(mask, 255, 0).astype(np.uint8), "L")
        .filter(ImageFilter.MaxFilter(size=25))
    ) > 0
    for mask in cloud_masks
]
cloud_alpha = np.maximum.reduce(cloud_source_alphas)
cloud_clear_mask = np.maximum.reduce(cloud_clear_masks)

# The exact foreground and cloud cutouts already exist. Remove their pixels from
# the skyline ownership map so every source pixel belongs to only one layer.
unassigned = objects & (foreground_alpha < 16) & (cloud_alpha < 16)
yy, xx = np.indices((HEIGHT, WIDTH))

asset_layout = [
    ("bridge", ASSETS / "scene-assets" / "bridge.png", 0, 757),
    ("ferry", ASSETS / "scene-assets" / "ferry.png", 355, 846),
    ("transamerica", ASSETS / "scene-assets" / "transamerica.png", 756, 660),
    ("sutro", ASSETS / "scene-assets" / "sutro.png", 1340, 558),
    ("right-hills", ASSETS / "scene-assets" / "right-hills.png", 1059, 799),
    ("left-cluster", ASSETS / "scene-assets" / "left-cluster.png", 607, 786),
    ("center-cluster", ASSETS / "scene-assets" / "center-skyline.png", 828, 775),
]

owned = {}
for name, source, left, top in asset_layout:
    source_alpha = Image.open(source).convert("RGBA").getchannel("A")
    canvas_alpha = Image.new("L", (WIDTH, HEIGHT), 0)
    canvas_alpha.paste(source_alpha, (left, top))
    canvas_alpha = canvas_alpha.filter(ImageFilter.MaxFilter(size=11))
    silhouette = np.asarray(canvas_alpha) > 6
    mask = unassigned & silhouette
    owned[name] = mask
    unassigned &= ~mask

# Grow the source-derived ownership seeds through every remaining illustrated
# architecture pixel. The generated assets are used only as semantic guides;
# the layer artwork itself always comes from ORIGINAL. This guarantees that all
# layers recompose to the canonical still without changing scale, color, or
# layout at the start of the scroll.
architecture_core = objects & (foreground_alpha < 16) & (cloud_alpha < 16)
architecture = np.asarray(
    Image.fromarray(np.where(architecture_core, 255, 0).astype(np.uint8), "L")
    .filter(ImageFilter.MaxFilter(size=31))
) > 0
cloud_exclusion = cloud_clear_mask
foreground_exclusion = np.asarray(
    Image.fromarray(foreground_alpha.astype(np.uint8), "L").filter(ImageFilter.MaxFilter(size=21))
) > 0
architecture &= ~cloud_exclusion & ~foreground_exclusion
layer_names = [name for name, *_ in asset_layout]
labels = np.full((HEIGHT, WIDTH), -1, dtype=np.int16)
for index, name in enumerate(layer_names):
    labels[owned[name]] = index

queue = deque()
seeded = labels >= 0
for dy, dx in ((0, -1), (0, 1), (-1, 0), (1, 0)):
    shifted_unowned = np.roll((architecture & ~seeded), shift=(-dy, -dx), axis=(0, 1))
    boundary = seeded & shifted_unowned
    ys, xs = np.where(boundary)
    queue.extend(zip(ys.tolist(), xs.tolist()))

while queue:
    y, x = queue.popleft()
    label = labels[y, x]
    for ny, nx in ((y, x - 1), (y, x + 1), (y - 1, x), (y + 1, x)):
        if 0 <= ny < HEIGHT and 0 <= nx < WIDTH and architecture[ny, nx] and labels[ny, nx] < 0:
            labels[ny, nx] = label
            queue.append((ny, nx))

# Tiny disconnected details such as isolated roof ornaments may not touch a
# seeded component. Assign them by the nearest semantic horizontal zone so no
# source pixel is dropped from the layered composition.
remaining = architecture & (labels < 0)
zone_labels = np.select(
    [xx < 520, xx < 675, xx < 790, xx < 900, xx < 1110, xx < 1330],
    [layer_names.index("bridge"), layer_names.index("ferry"), layer_names.index("left-cluster"),
     layer_names.index("transamerica"), layer_names.index("center-cluster"), layer_names.index("right-hills")],
    default=layer_names.index("sutro"),
)
labels[remaining] = zone_labels[remaining]

# The first departure is a clean left/right split. Keep every visible source
# pixel on the same side of the natural gap between Transamerica and the dark
# center tower so no building fragment is pulled in the opposite direction.
left_label_ids = [layer_names.index(name) for name in ("bridge", "ferry", "left-cluster", "transamerica")]
right_label_ids = [layer_names.index(name) for name in ("center-cluster", "right-hills", "sutro")]
left_side = architecture & (xx < 850)
right_side = architecture & ~left_side
labels[left_side & np.isin(labels, right_label_ids)] = layer_names.index("transamerica")
labels[right_side & np.isin(labels, left_label_ids)] = layer_names.index("center-cluster")
owned = {name: labels == index for index, name in enumerate(layer_names)}
unassigned = architecture & (labels < 0)

# The bay is a separate, exact-source layer. Its soft mask stays underneath all
# architectural masks and follows the visible water area rather than a page-wide rectangle.
water_shape = (
    (yy > 965)
    & (xx > 180)
    & (xx < 925)
    & sky
)
water_mask_image = Image.fromarray(np.where(water_shape, 255, 0).astype(np.uint8), "L")
water_mask_image = water_mask_image.filter(ImageFilter.GaussianBlur(radius=5))
water_mask = np.asarray(water_mask_image) > 8

for name, mask in owned.items():
    save_source_layer(name, mask)

# Complete, independently movable assets. These are placed on the same
# 1486x1058 artboard so the browser never has to crop a building or infer its
# position. They are used during motion; the canonical original remains the
# exact resting reference at scroll position zero.
for name, source, left, top in asset_layout:
    asset = Image.open(source).convert("RGBA")
    if name == "bridge":
        bridge_rgba = np.asarray(asset).copy()
        red = bridge_rgba[:, :, 0].astype(np.int16)
        blue = bridge_rgba[:, :, 2].astype(np.int16)
        alpha = bridge_rgba[:, :, 3]
        contaminated = (alpha > 0) & (red > 145) & (blue > red * 0.52)
        bridge_rgba[contaminated, 1] = np.maximum(
            bridge_rgba[contaminated, 1],
            np.clip(red[contaminated] * 0.22, 0, 255).astype(np.uint8),
        )
        bridge_rgba[contaminated, 2] = np.clip(red[contaminated] * 0.12, 0, 255).astype(np.uint8)
        asset = Image.fromarray(bridge_rgba, "RGBA")
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    canvas.alpha_composite(asset, (left, top))
    canvas.save(OUT / f"generated-{name}.png", optimize=True)

save_source_layer("water", water_mask)

# Split the exact foreground only through the natural center valley. The two
# transparent files still recompose to the original artwork at rest.
foreground_rgba = original.copy()
foreground_rgba[:, :, 3] = np.where(foreground_alpha > 5, 255, 0).astype(np.uint8)
foreground_left = foreground_rgba.copy()
foreground_right = foreground_rgba.copy()
foreground_left[:, 744:, 3] = 0
foreground_right[:, :744, 3] = 0
foreground_left[foreground_left[:, :, 3] == 0, :3] = 0
foreground_right[foreground_right[:, :, 3] == 0, :3] = 0
Image.fromarray(foreground_left, "RGBA").save(OUT / "foreground-left.png", optimize=True)
Image.fromarray(foreground_right, "RGBA").save(OUT / "foreground-right.png", optimize=True)

# Preserve the already-clean exact assets as full-canvas semantic source layers.
for source, mask in zip(cloud_paths, cloud_masks):
    save_source_layer(source.stem, mask)

# Build an exact resting environment plate. Pixels that never move are copied
# verbatim from the canonical illustration. Only pixels owned by moving layers
# are replaced underneath with the clean sky/bay plate.
clean_sky = np.asarray(CLEAN_SKY).astype(np.float32)
environment = np.asarray(ENVIRONMENT).astype(np.float32)
water_blend = np.clip((yy.astype(np.float32) - 925) / 70, 0, 1)[:, :, None]
clean_plate = np.round(clean_sky * (1 - water_blend) + environment * water_blend).astype(np.uint8)
base = original.copy()
moving_mask = architecture | (foreground_alpha > 5) | cloud_clear_mask
base[moving_mask] = clean_plate[moving_mask]
Image.fromarray(base, "RGBA").save(OUT / "environment-base.png", optimize=True)

# Static proof image and numeric verification.
composite = Image.fromarray(base, "RGBA")
for name in [
    "water",
    "bridge",
    "left-cluster",
    "transamerica",
    "center-cluster",
    "right-hills",
    "sutro",
    "ferry",
    "cloud-left-top",
    "cloud-right-top",
    "cloud-left-low",
    "cloud-right-low",
    "foreground-left",
    "foreground-right",
]:
    composite.alpha_composite(Image.open(OUT / f"{name}.png").convert("RGBA"))

composite.save(OUT / "static-recomposition.png", optimize=True)
diff = np.abs(np.asarray(composite).astype(np.int16) - original.astype(np.int16))
print({
    "canvas": [WIDTH, HEIGHT],
    "max_channel_error": int(diff.max()),
    "mean_channel_error": float(diff.mean()),
    "unassigned_object_pixels": int(unassigned.sum()),
    "changed_pixels": int(np.any(diff > 0, axis=2).sum()),
})

# Convert the image-generated complete bridge from its preview checkerboard to
# a true transparent cutout. It sits underneath the exact-source bridge pixels
# and is only revealed when foreground foliage moves away.
bridge_source_path = ASSETS / "layers" / "bridge-complete-v2-source.png"
if bridge_source_path.exists():
    bridge = np.asarray(Image.open(bridge_source_path).convert("RGB"))
    high = bridge.max(axis=2).astype(np.int16)
    low = bridge.min(axis=2).astype(np.int16)
    chroma = high - low
    alpha = np.where((chroma < 16) & (high > 204), 0, 255).astype(np.uint8)
    ys, xs = np.where(alpha > 0)
    if len(xs):
        pad = 4
        left = max(0, int(xs.min()) - pad)
        top = max(0, int(ys.min()) - pad)
        right = min(bridge.shape[1], int(xs.max()) + pad + 1)
        bottom = min(bridge.shape[0], int(ys.max()) + pad + 1)
        rgba = np.dstack([bridge, alpha])[top:bottom, left:right]
        Image.fromarray(rgba, "RGBA").save(OUT / "bridge-complete.png", optimize=True)

# ImageGen's preview for the complete right hillside contains a visible
# checkerboard baked into the RGB pixels. Remove only the pale neutral region
# that is connected to the artboard edge. This keeps white house walls and
# paper highlights intact while turning the preview background into real alpha.
right_hills_source_path = OUT / "right-hills-complete-v2-source.png"
if right_hills_source_path.exists():
    hills = np.asarray(Image.open(right_hills_source_path).convert("RGB"))
    high = hills.max(axis=2).astype(np.int16)
    low = hills.min(axis=2).astype(np.int16)
    candidate = ((high - low) < 14) & (low > 220)
    background = np.zeros(candidate.shape, dtype=bool)
    queue = deque()

    def add_hills_background(y: int, x: int) -> None:
        if (
            0 <= y < hills.shape[0]
            and 0 <= x < hills.shape[1]
            and candidate[y, x]
            and not background[y, x]
        ):
            background[y, x] = True
            queue.append((y, x))

    for x in range(hills.shape[1]):
        add_hills_background(0, x)
        add_hills_background(hills.shape[0] - 1, x)
    for y in range(hills.shape[0]):
        add_hills_background(y, 0)
        add_hills_background(y, hills.shape[1] - 1)

    while queue:
        y, x = queue.popleft()
        add_hills_background(y, x - 1)
        add_hills_background(y, x + 1)
        add_hills_background(y - 1, x)
        add_hills_background(y + 1, x)

    alpha = np.where(background, 0, 255).astype(np.uint8)
    # Soften the cutout edge by one pixel without changing the illustration.
    alpha_image = Image.fromarray(alpha, "L").filter(ImageFilter.GaussianBlur(radius=0.55))
    rgba = Image.fromarray(np.dstack([hills, np.asarray(alpha_image)]), "RGBA")
    rgba.save(OUT / "right-hills-complete-v2.png", optimize=True)
