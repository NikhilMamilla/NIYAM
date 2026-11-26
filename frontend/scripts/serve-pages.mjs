// Serve dist/ the way GitHub Pages does: under /NIYAM/, and 404.html with status 404 for any path that is not a
// file (that is how /NIYAM/app opens the client-side router). For e2e-static only; run `npm run build:pages` first.
import { createServer } from "node:http";
import { readFile, stat } from "node:fs/promises";
import { extname, resolve, sep } from "node:path";

const BASE = "/NIYAM/";
const ROOT = resolve("dist");
const PORT = Number(process.env.PORT || 4180);
const TYPES = {
  ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".mjs": "text/javascript", ".css": "text/css",
  ".json": "application/json", ".wasm": "application/wasm", ".png": "image/png", ".webp": "image/webp",
  ".svg": "image/svg+xml", ".woff2": "font/woff2", ".pdf": "application/pdf", ".txt": "text/plain",
};

async function fileFor(urlPath) {
  if (!urlPath.startsWith(BASE)) return null;
  let full = resolve(ROOT, `.${urlPath.slice(BASE.length - 1)}`);
  if (full !== ROOT && !full.startsWith(ROOT + sep)) return null; // no way out of dist/
  try {
    if ((await stat(full)).isDirectory()) full = resolve(full, "index.html");
    return (await stat(full)).isFile() ? full : null;
  } catch {
    return null;
  }
}

createServer(async (req, res) => {
  const file = await fileFor(decodeURIComponent(new URL(req.url ?? "/", "http://x").pathname));
  const served = file ?? resolve(ROOT, "404.html");
  res.writeHead(file ? 200 : 404, { "content-type": TYPES[extname(served)] ?? "application/octet-stream" });
  res.end(await readFile(served));
}).listen(PORT, () => console.log(`GitHub Pages stand-in: http://localhost:${PORT}${BASE}`));
