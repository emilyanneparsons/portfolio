const sharp = require("sharp");

const input = process.argv[2];
const output = process.argv[3];
const skyOutput = process.argv[4];

if (!input || !output) {
  throw new Error("Usage: node scripts/extract-sky.js input.png output.png");
}

async function main() {
  const image = sharp(input).ensureAlpha();
  const { data, info } = await image.raw().toBuffer({ resolveWithObject: true });
  const { width, height, channels } = info;
  const pixels = width * height;
  const candidate = new Uint8Array(pixels);
  const sky = new Uint8Array(pixels);

  for (let i = 0; i < pixels; i += 1) {
    const offset = i * channels;
    const r = data[offset];
    const g = data[offset + 1];
    const b = data[offset + 2];
    candidate[i] =
      b > 145 && g > 112 && r < 165 && b - r > 48 && g - r > 24
        ? 1
        : 0;
  }

  const queue = new Int32Array(pixels);
  let head = 0;
  let tail = 0;

  function enqueue(index) {
    if (candidate[index] && !sky[index]) {
      sky[index] = 1;
      queue[tail++] = index;
    }
  }

  for (let x = 0; x < width; x += 1) {
    enqueue(x);
    enqueue((height - 1) * width + x);
  }
  for (let y = 0; y < height; y += 1) {
    enqueue(y * width);
    enqueue(y * width + width - 1);
  }

  while (head < tail) {
    const index = queue[head++];
    const x = index % width;
    const y = Math.floor(index / width);
    if (x > 0) enqueue(index - 1);
    if (x + 1 < width) enqueue(index + 1);
    if (y > 0) enqueue(index - width);
    if (y + 1 < height) enqueue(index + width);
  }

  for (let i = 0; i < pixels; i += 1) {
    if (sky[i]) {
      data[i * channels + 3] = 0;
    }
  }

  await sharp(data, { raw: info }).png().toFile(output);

  if (skyOutput) {
    await sharp(input)
      .extract({ left: 320, top: 0, width: 800, height: 600 })
      .resize(width, height, { fit: "fill" })
      .webp({ quality: 90, effort: 5 })
      .toFile(skyOutput);
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
