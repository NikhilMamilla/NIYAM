import type { Page } from "@playwright/test";

export interface ColourStats {
  total: number;
  red: number;
  amber: number;
  grey: number;
  blue: number;
  /** red/amber blended with the pale background: how translucent rooms look */
  pinkRed: number;
  paleAmber: number;
  /** centre of the red pixels, in screenshot pixels, or null */
  redCentre: { x: number; y: number } | null;
}

/** Decode a PNG screenshot in the browser and count pixels by verdict colour (shading-tolerant ranges). */
export async function colourStats(page: Page, png: Buffer): Promise<ColourStats> {
  const dataUrl = `data:image/png;base64,${png.toString("base64")}`;
  return page.evaluate(async (src) => {
    const img = new Image();
    img.src = src;
    await img.decode();
    const canvas = document.createElement("canvas");
    canvas.width = img.width;
    canvas.height = img.height;
    const ctx = canvas.getContext("2d")!;
    ctx.drawImage(img, 0, 0);
    const { data } = ctx.getImageData(0, 0, img.width, img.height);
    const stats = { total: img.width * img.height, red: 0, amber: 0, grey: 0, blue: 0, pinkRed: 0, paleAmber: 0, redCentre: null as null | { x: number; y: number } };
    let sx = 0;
    let sy = 0;
    const reds: number[] = [];
    for (let i = 0; i < data.length; i += 4) {
      const r = data[i]!, g = data[i + 1]!, b = data[i + 2]!;
      if (r > 120 && g < 70 && b < 70) {
        stats.red += 1;
        const p = i / 4;
        reds.push(p);
        sx += p % img.width;
        sy += Math.floor(p / img.width);
      } else if (r > 150 && g > 90 && g < 200 && b < 70) stats.amber += 1;
      else if (b > 150 && r < 90 && g < 130) stats.blue += 1;
      else if (r > 200 && r - g > 60 && g > 100 && Math.abs(g - b) < 30) stats.pinkRed += 1;
      else if (r > 225 && g > 170 && g < 225 && b > 90 && b < 175 && r - b > 70) stats.paleAmber += 1;
      else if (Math.abs(r - g) < 12 && Math.abs(g - b) < 14 && r > 100 && r < 180) stats.grey += 1;
    }
    if (stats.red) {
      // the red pixel nearest the centroid: always on a red element, unlike the centroid itself
      const cx = sx / stats.red, cy = sy / stats.red;
      let best = reds[0]!, bestD = Infinity;
      for (const p of reds) {
        const d = (p % img.width - cx) ** 2 + (Math.floor(p / img.width) - cy) ** 2;
        if (d < bestD) { bestD = d; best = p; }
      }
      stats.redCentre = { x: best % img.width, y: Math.floor(best / img.width) };
    }
    return stats;
  }, dataUrl);
}
