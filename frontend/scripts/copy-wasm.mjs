// Copy the installed web-ifc wasm into public/ so the viewer never fetches it from a CDN.
import { copyFileSync, mkdirSync } from "node:fs";

mkdirSync("public/web-ifc", { recursive: true });
// single-threaded build only: the multi-threaded one needs a cross-origin-isolated page, which this app is not
for (const name of ["web-ifc.wasm"]) {
  copyFileSync(`node_modules/web-ifc/${name}`, `public/web-ifc/${name}`);
}
console.log("copied web-ifc wasm to public/web-ifc/");
