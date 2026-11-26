import { defineConfig } from "@playwright/test";

// The GitHub Pages build with no backend. Locally it builds dist/ (npm run build:pages) and serves it like Pages;
// with LIVE_URL set it checks the deployed site instead, e.g. LIVE_URL=https://nikhilmamilla.github.io/NIYAM/
const live = process.env.LIVE_URL;

export default defineConfig({
  testDir: "e2e-static",
  timeout: 180_000,
  expect: { timeout: 30_000 },
  workers: 1,
  reporter: [["list"]],
  use: {
    baseURL: live ?? "http://localhost:4180/NIYAM/",
    viewport: { width: 1440, height: 900 },
    acceptDownloads: true,
    launchOptions: { args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] },
  },
  webServer: live ? undefined : {
    command: "npm run build:pages && node scripts/serve-pages.mjs",
    url: "http://localhost:4180/NIYAM/",
    reuseExistingServer: false,
    timeout: 300_000,
  },
});
