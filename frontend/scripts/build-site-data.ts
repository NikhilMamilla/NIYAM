// npm run site-data: regenerate src/data/site-data.json from the committed result files.
import { writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { buildSiteData } from "../src/data/buildSiteData.ts";

const root = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const out = join(root, "frontend", "src", "data", "site-data.json");
writeFileSync(out, JSON.stringify(buildSiteData(root), null, 1) + "\n", "utf-8");
console.log(`wrote ${out}`);
