const sharp = require("sharp");
const path = require("path");

const input = process.argv[2];
const outputDirectory = process.argv[3];

if (!input || !outputDirectory) {
  throw new Error("Usage: node scripts/extract-depth-sheet.js sheet.png output-directory");
}

const cells = [
  ["bridge", 0, 120, 450, 380],
  ["ferry", 440, 170, 410, 320],
  ["left-cluster", 840, 170, 420, 330],
  ["transamerica", 1260, 20, 230, 480],
  ["center-skyline", 20, 555, 480, 350],
  ["sutro", 500, 520, 180, 390],
  ["right-hills", 690, 570, 480, 340],
  ["bushes", 1140, 700, 396, 220],
];

async function main() {
  const { data, info } = await sharp(input).raw().toBuffer({ resolveWithObject: true });
  const rgba = Buffer.alloc(info.width * info.height * 4);
  const bridgeRgba = Buffer.alloc(info.width * info.height * 4);
  const background = [242, 10, 239];

  const writePixel = (buffer, outputOffset, r, g, b, alpha) => {
    if (alpha > 0 && alpha < 255) {
      const amount = alpha / 255;
      buffer[outputOffset] = Math.max(0, Math.min(255, Math.round((r - (1 - amount) * background[0]) / amount)));
      buffer[outputOffset + 1] = Math.max(0, Math.min(255, Math.round((g - (1 - amount) * background[1]) / amount)));
      buffer[outputOffset + 2] = Math.max(0, Math.min(255, Math.round((b - (1 - amount) * background[2]) / amount)));
    } else {
      buffer[outputOffset] = r;
      buffer[outputOffset + 1] = g;
      buffer[outputOffset + 2] = b;
    }
    buffer[outputOffset + 3] = alpha;
  };

  for (let i = 0; i < info.width * info.height; i += 1) {
    const inputOffset = i * info.channels;
    const outputOffset = i * 4;
    const r = data[inputOffset];
    const g = data[inputOffset + 1];
    const b = data[inputOffset + 2];
    const magenta = Math.min(r, b) - g - Math.abs(r - b) * 0.45;
    let alpha = 255;
    let bridgeAlpha = 255;

    if (magenta >= 12) {
      alpha = 0;
    } else if (magenta > 0) {
      alpha = Math.round(255 * (12 - magenta) / 12);
    }

    const balance = Math.abs(r - b);
    if (r > 188 && b > 176 && g < 92 && balance < 68) {
      bridgeAlpha = 0;
    } else if (r > 162 && b > 148 && g < 128 && balance < 88) {
      const strength = Math.min(
        1,
        Math.max(
          0,
          Math.min((r - 162) / 26, (b - 148) / 28, (128 - g) / 36, (88 - balance) / 34),
        ),
      );
      bridgeAlpha = Math.round(255 * (1 - strength));
    }

    writePixel(rgba, outputOffset, r, g, b, alpha);
    writePixel(bridgeRgba, outputOffset, r, g, b, bridgeAlpha);
  }

  for (const [name, left, top, width, height] of cells) {
    const cell = Buffer.alloc(width * height * 4);
    const source = name === "bridge" ? bridgeRgba : rgba;

    for (let row = 0; row < height; row += 1) {
      const sourceStart = ((top + row) * info.width + left) * 4;
      const sourceEnd = sourceStart + width * 4;
      source.copy(cell, row * width * 4, sourceStart, sourceEnd);
    }

    await sharp(cell, {
      raw: { width, height, channels: 4 },
    })
      .trim({ background: { r: 0, g: 0, b: 0, alpha: 0 } })
      .png({ compressionLevel: 9, adaptiveFiltering: true })
      .toFile(path.join(outputDirectory, `${name}.png`));
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
