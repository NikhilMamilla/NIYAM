// Build the GitHub Pages site: base path /NIYAM/ and static demo mode on. VITE_API_URL passes through when set
// (a deployed backend); without it, or when that backend is down, the app shows the saved sample results.
import { execSync } from "node:child_process";

execSync("npm run build", {
  stdio: "inherit",
  env: { ...process.env, PAGES_BASE: process.env.PAGES_BASE || "/NIYAM/", VITE_STATIC_DEMO: "1" },
});
