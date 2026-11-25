// Render the project documents (Markdown in the repo) as readable A4 PDFs in public/downloads/.
// Run: npm run docs:pdf   (needs the Chromium that Playwright already installed for the e2e tests)
import { readFileSync, mkdirSync, writeFileSync, rmSync } from "node:fs";
import { basename, resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { marked } from "marked";
import { chromium } from "@playwright/test";

const DOCS = [
  { src: "../README.md", title: "NIYAM: project overview", lead: "What NIYAM is, how it works, where it stands today, and how to run it." },
  { src: "../docs/evaluation.md", title: "Evaluation: method and metrics", lead: "How rule compilation is scored on test buildings the verifier gate never sees, and what the first real run showed." },
  { src: "../docs/spec-backlog.md", title: "Rule specs and what they cannot express", lead: "Which bye-law sentences became machine checks, and why the rest do not fit a single-element template." },
  { src: "../docs/real-models.md", title: "Real IFC models: what the audit could check", lead: "Two real building models run through the audit, and the data they lack." },
  { src: "../docs/modelling-profile.md", title: "What a model must contain", lead: "The data an IFC model needs before NIYAM can check it." },
  { src: "../docs/geometric-gate.md", title: "The geometric gate and its sandbox", lead: "How computed-value checks are run safely, and what the sandbox does not enforce." },
  { src: "../docs/review/REVIEWER_GUIDE.md", title: "Reviewer guide", lead: "How a domain expert reviews the draft rules and returns decisions." },
  { src: "../docs/frontend.md", title: "Web app notes", lead: "The stack, the 3D view, the design system, and the checks to repeat in your own browser." },
  { src: "../docs/specgen.md", title: "Rule specs and the generator", lead: "How one small spec file becomes an IDS file or a Python check, and the five templates a rule can use." },
  { src: "../docs/audit.md", title: "Audit engine and exports", lead: "How a model is audited against the draft rulepack, and what the JSON, HTML and BCF outputs contain." },
  { src: "../docs/samples.md", title: "Synthetic sample buildings", lead: "The generated test models behind the samples, and what each one is built to show." },
  { src: "../docs/notes-ids-expressiveness.md", title: "Can IDS express numeric limits?", lead: "A tested note on which numeric lower bounds IDS 1.0 can and cannot state." },
  { src: "../docs/notes-geometric-spike.md", title: "Geometric tier spike", lead: "Which bye-law sentences compare a value that has to be computed from geometry." },
  { src: "../docs/notes-ifctester.md", title: "ifctester notes", lead: "Verified notes on building and running IDS files with ifctester." },
  { src: "../docs/corpus-candidates.md", title: "Corpus candidates", lead: "Keyword-scored candidate clauses from the bye-laws. Nothing here is selected; every clause stays a candidate until a person marks it." },
  { src: "../STATUS.md", title: "Project status and known issues", lead: "What is final, what is still open, and the exact commands to reproduce the tests and the re-score." },
  { src: "../THIRD_PARTY_NOTICES.md", title: "Third-party notices", lead: "Every shipped package, font, copied component and data file, with its licence and source." },
  { src: "../docs/sources.md", title: "Sources for the regulatory facts", lead: "The pages behind each date and regulation on the landing page, with access dates." },
];

const font = (name, file, weight) =>
  `@font-face{font-family:"${name}";src:url("${pathToFileURL(resolve("public/fonts", file)).href}") format("woff2");font-weight:${weight};}`;

const CSS = `
${font("Plex Sans", "ibm-plex-sans-latin-400-normal.woff2", 400)}
${font("Plex Sans", "ibm-plex-sans-latin-500-normal.woff2", 500)}
${font("Plex Sans", "ibm-plex-sans-latin-600-normal.woff2", 600)}
${font("Plex Mono", "ibm-plex-mono-latin-400-normal.woff2", 400)}
${font("Instrument Serif", "instrument-serif-latin-400-normal.woff2", 400)}
:root{--ink:#191F30;--ink2:#3d4560;--ink3:#667089;--line:#3447C7;--rule:#d9d4c6;--paper:#faf7ef;}
*{box-sizing:border-box}
body{margin:0;font:400 10.5pt/1.62 "Plex Sans",sans-serif;color:var(--ink);}
.cover{padding:6mm 0 7mm;border-bottom:1.5px solid var(--ink);margin-bottom:8mm}
.brand{font:400 11pt "Instrument Serif",serif;letter-spacing:.28em;text-transform:uppercase;color:var(--line)}
.cover h1{font:400 30pt/1.08 "Instrument Serif",serif;letter-spacing:-.01em;margin:5mm 0 3mm}
.lead{font-size:12pt;line-height:1.5;color:var(--ink2);margin:0 0 4mm;max-width:150mm}
.note{display:inline-block;font:500 8.5pt "Plex Sans";padding:2mm 3.2mm;border:1px solid #c9a24a;background:#f8efd6;color:#6b4e0a;border-radius:3mm}
.toc{margin:0 0 9mm;padding:5mm 6mm;border:1px solid var(--rule);background:var(--paper);border-radius:3mm;break-inside:avoid}
.toc h2{font:600 8.5pt "Plex Sans";letter-spacing:.14em;text-transform:uppercase;color:var(--ink3);margin:0 0 2.5mm;border:0;padding:0}
.toc ol{margin:0;padding-left:5mm;columns:2;column-gap:10mm;font-size:10pt}
.toc li{margin:0 0 1.2mm;break-inside:avoid}
h2{font:400 19pt/1.2 "Instrument Serif",serif;margin:10mm 0 3mm;padding-top:3mm;border-top:1px solid var(--rule);break-after:avoid}
h3{font:600 11.5pt/1.3 "Plex Sans";margin:6.5mm 0 2mm;color:var(--ink);break-after:avoid}
h4{font:600 10.5pt "Plex Sans";margin:5mm 0 1.5mm;color:var(--ink2);break-after:avoid}
p{margin:0 0 3mm;orphans:3;widows:3}
a{color:var(--line);text-decoration:none}
strong{font-weight:600}
ul,ol{margin:0 0 3.5mm;padding-left:6mm}
li{margin:0 0 1.4mm}
li>p{margin-bottom:1.5mm}
code{font:400 8.8pt "Plex Mono",monospace;background:#efeadb;padding:.3mm 1.3mm;border-radius:1.2mm;color:#2a3150;overflow-wrap:anywhere}
pre{margin:0 0 4mm;padding:3.5mm 4mm;background:#191F30;color:#eef0fa;border-radius:2.5mm;overflow:hidden;white-space:pre-wrap;overflow-wrap:anywhere;font-size:8.3pt;line-height:1.5}
pre code{background:none;color:inherit;padding:0;font-size:inherit;overflow-wrap:anywhere}
table{width:100%;border-collapse:collapse;margin:1mm 0 5mm;font-size:9.3pt;line-height:1.45}
thead th{background:var(--ink);color:#fff;font-weight:600;text-align:left;padding:2.2mm 3mm}
tbody td,tbody th{padding:2.2mm 3mm;border-bottom:1px solid var(--rule);vertical-align:top;text-align:left}
tbody tr:nth-child(even){background:#f6f2e7}
tr{break-inside:avoid}
blockquote{margin:0 0 4mm;padding:2mm 4.5mm;border-left:3px solid var(--line);background:#eef0fb;color:var(--ink2)}
hr{border:0;border-top:1px solid var(--rule);margin:6mm 0}
`;

const slug = (s) => s.toLowerCase().replace(/<[^>]+>/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");

function render(md) {
  const html = marked.parse(md.replace(/\r\n/g, "\n").replace(/^# .*\n/, ""), { gfm: true });
  const heads = [...html.matchAll(/<h2>(.*?)<\/h2>/g)].map((m) => m[1]);
  const body = html.replace(/<h2>(.*?)<\/h2>/g, (_, t) => `<h2 id="${slug(t)}">${t}</h2>`);
  const toc = heads.length >= 4
    ? `<nav class="toc"><h2>Contents</h2><ol>${heads.map((h) => `<li>${h}</li>`).join("")}</ol></nav>`
    : "";
  return { body, toc };
}

mkdirSync("public/downloads", { recursive: true });
const tmp = resolve(".pdf-tmp");
mkdirSync(tmp, { recursive: true });
const browser = await chromium.launch();
try {
  for (const d of DOCS) {
    const { body, toc } = render(readFileSync(d.src, "utf8"));
    const file = resolve(tmp, basename(d.src, ".md") + ".html");
    writeFileSync(file, `<!doctype html><html lang="en"><meta charset="utf-8"><title>${d.title}</title><style>${CSS}</style>
<header class="cover"><div class="brand">NIYAM</div><h1>${d.title}</h1><p class="lead">${d.lead}</p>
<span class="note">Research prototype · every rule is a draft, not human-reviewed</span></header>${toc}<main>${body}</main></html>`);
    const page = await browser.newPage();
    await page.goto(pathToFileURL(file).href);
    await page.evaluate(() => document.fonts.ready);
    const out = `public/downloads/${basename(d.src, ".md")}.pdf`;
    await page.pdf({
      path: out, format: "A4", printBackground: true,
      margin: { top: "18mm", bottom: "20mm", left: "20mm", right: "20mm" },
      displayHeaderFooter: true, headerTemplate: "<span></span>",
      footerTemplate: `<div style="width:100%;font:8pt 'Helvetica',sans-serif;color:#667089;padding:0 20mm;display:flex;justify-content:space-between"><span>NIYAM · ${d.title}</span><span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>`,
    });
    await page.close();
    console.log("wrote", out);
  }
} finally {
  await browser.close();
  rmSync(tmp, { recursive: true, force: true });
}
