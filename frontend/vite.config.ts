import { copyFileSync } from "node:fs";
import react from "@vitejs/plugin-react";
import { defineConfig, type Plugin } from "vitest/config";

// GitHub Pages serves the site under /NIYAM/ (set by scripts/build-pages.mjs); local dev and builds use "/".
const pagesBase = process.env.PAGES_BASE;

// Pages has no rewrite rules: it serves 404.html for any unknown path, so a copy of index.html there lets the
// client-side router open /NIYAM/app and every other deep link directly.
const spaFallback: Plugin = {
  name: "pages-spa-fallback",
  apply: "build",
  closeBundle() {
    copyFileSync("dist/index.html", "dist/404.html");
  },
};

export default defineConfig({
  base: pagesBase || "/",
  plugins: [react(), ...(pagesBase ? [spaFallback] : [])],
  server: {
    port: 5173,
    strictPort: true,
    proxy: { "/api": "http://127.0.0.1:8000" },
    // the readiness IDS is imported from docs/ (one source of truth), outside the frontend folder
    fs: { allow: [".."] },
  },
  test: {
    include: ["src/**/*.test.{ts,tsx}"],
    environment: "node",
  },
});
