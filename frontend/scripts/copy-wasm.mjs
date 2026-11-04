// Copy the installed web-ifc wasm into public/ so the viewer never fetches it from a CDN.
import { copyFileSync, mkdirSync } from "node:fs";

mkdirSync("public/web-ifc", { recursive: true });
for (const name of ["web-ifc.wasm", "web-ifc-mt.wasm"]) {
  copyFileSync(`node_modules/web-ifc/${name}`, `public/web-ifc/${name}`);
}
console.log("copied web-ifc wasm to public/web-ifc/");
