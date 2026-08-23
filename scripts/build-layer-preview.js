const sharp = require("sharp");

const CANVAS = { width: 1486, height: 1058 };

const layers = [
  ["assets/scene-assets/bridge.png", 0, 757],
  ["assets/scene-assets/left-cluster.png", 607, 786],
  ["assets/scene-assets/center-skyline.png", 828, 775],
  ["assets/scene-assets/transamerica.png", 756, 660],
  ["assets/scene-assets/right-hills.png", 1059, 799],
  ["assets/scene-assets/sutro.png", 1340, 558],
  ["assets/scene-assets/ferry.png", 355, 846],
  ["assets/scroll-layers/cloud-left-top.webp", 0, 0],
  ["assets/scroll-layers/cloud-right-top.webp", 0, 0],
  ["assets/scroll-layers/cloud-left-low.webp", 0, 0],
  ["assets/scroll-layers/cloud-right-low.webp", 0, 0],
  ["assets/homepage-foreground-bushes.png", 0, 0],
];

async function main() {
  const background = await sharp("assets/layers/environment-plate-v2.png")
    .resize(CANVAS.width, CANVAS.height, { fit: "fill" })
    .png()
    .toBuffer();

  await sharp(background)
    .composite(layers.map(([input, left, top]) => ({ input, left, top })))
    .png({ compressionLevel: 9 })
    .toFile("assets/layers/static-composite-preview-v1.png");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
