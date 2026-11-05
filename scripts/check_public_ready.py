"""Is the repository safe to make public? Scans every git-tracked file and the full history (git log -p --all,
streamed) for likely secrets, personal absolute paths, committed databases/caches/build or run output, and files
over 5 MB. Matched secret values are never printed in full: only the first 4 characters.

Usage (from the repository root):  python scripts/check_public_ready.py [--no-history]
Exit code 1 if any secret is found (in the tree or in history); 0 otherwise. Other findings are warnings."""

import hashlib
import math
import re
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAX_BYTES = 5 * 1024 * 1024
KEY_PATTERNS = [
    re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}"), re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9]{20,}"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"), re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}"), re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"), re.compile(r"\bhf_[A-Za-z0-9]{30,}"), re.compile(r"\bglpat-[A-Za-z0-9_-]{20,}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----"),
]
ASSIGNED = re.compile(r"(?i)(?:key|token|secret|passw(?:or)?d)[\w-]*\s*[:=]\s*['\"]?([A-Za-z0-9_\-+/=.]{20,})")
PERSONAL = re.compile(r"(?i)(?:[A-Z]:[\\/]+Users[\\/]+(?!<)[^\\/\s'\"]+|[A-Z]:[\\/]+Desktop|/home/(?!<)[a-z][\w.-]+|"
                      r"/Users/(?!<|Shared)[A-Za-z][\w.-]+)")
# The scanner's own test inputs, committed once in history (2fe241c) before they were built at run time. Matched by
# exact SHA-256 of file path and value, so the same value anywhere else (e.g. a real key's header) is still reported.
SYNTHETIC_SHA256 = {  # sha256(path + NUL + value)
    "46e204fd96cbb30847543091db5520a7aa105d17cd373914aea450f1934b22d2",
    "7906690b7a3ac2f2c6dbc8cc35adbe4802b12413930acd1f859bdc945f536c4a",
    "a1f83fd54d2d61c641458356a2160d279a9c069f088dd05171c3624aeef08b03",
    "b30c581eee10bf800720cbc6dedde8f553937565eac603f05d0199209eacbabc",
}
# deliberately fake keys in tests say so in the value; they are listed, but are not secrets
PLACEHOLDER = re.compile(r"(?i)test|fake|dummy|example|placeholder")
CODE_EXPRESSION = re.compile(r"[a-z_][a-z0-9_]*(?:\.[a-z_][a-z0-9_]*)+")
ENV_LINE = re.compile(r"^(?:HOSTED_LLM_API_KEY|OPENAI_API_KEY|ANTHROPIC_API_KEY)\s*=\s*\S+")


@dataclass
class Finding:
    kind: str  # secret | personal_path | file
    path: str
    line: int
    snippet: str
    where: str = "tree"


def entropy(s: str) -> float:
    counts = Counter(s)
    return -sum(c / len(s) * math.log2(c / len(s)) for c in counts.values())


def mask(value: str) -> str:
    return value[:4] + "…" + f"({len(value)} chars)"


def scan_text(path: str, text: str, where: str = "tree") -> list[Finding]:
    findings = []
    for n, line in enumerate(text.splitlines(), start=1):
        hits = [m.group(0) for p in KEY_PATTERNS for m in p.finditer(line)]
        hits += [m.group(1) for m in ASSIGNED.finditer(line) if entropy(m.group(1)) >= 3.5 and not m.group(1).isdigit()]
        if ENV_LINE.match(line):
            hits.append(line.split("=", 1)[1].strip())
        for value in dict.fromkeys(hits):
            if CODE_EXPRESSION.fullmatch(value):
                continue  # e.g. api_key=s.hosted_llm_api_key: a variable, not a value
            synthetic = hashlib.sha256(f"{path}\0{value}".encode()).hexdigest() in SYNTHETIC_SHA256
            kind = "test_placeholder" if PLACEHOLDER.search(value) or synthetic else "secret"
            findings.append(Finding(kind, path, n, mask(value), where))
        for m in PERSONAL.finditer(line):
            if hashlib.sha256(f"{path}\0{m.group(0)}".encode()).hexdigest() not in SYNTHETIC_SHA256:
                findings.append(Finding("personal_path", path, n, m.group(0), where))
    return findings


def path_problems(path: str, size: int) -> list[str]:
    p = path.replace("\\", "/")
    problems = []
    if p.endswith((".db", ".sqlite", ".sqlite3")):
        problems.append("committed database")
    if p.endswith(".pyc") or "/__pycache__/" in f"/{p}":
        problems.append("compiled Python cache")
    if "node_modules/" in f"/{p}":
        problems.append("node_modules")
    if re.search(r"(^|/)(dist|build|playwright-report|test-results)/", p):
        problems.append("build or test output")
    if p.startswith(("eval/runs/", "eval/results/dryrun-")):
        problems.append("run output")
    if p.startswith("backend/data/"):
        problems.append("local data (backend/data)")
    if p == ".env" or p.endswith("/.env"):
        problems.append("environment file")
    if size > MAX_BYTES:
        problems.append("larger than 5 MB")
    return problems


def tracked_files() -> list[str]:
    out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True).stdout
    return [p for p in out.decode("utf-8").split("\0") if p]


def scan_tree() -> list[Finding]:
    findings = []
    for rel in tracked_files():
        path = ROOT / rel
        if not path.is_file():
            continue
        size = path.stat().st_size
        findings += [Finding("file", rel, 0, problem) for problem in path_problems(rel, size)]
        if size > MAX_BYTES or path.suffix.lower() in {".png", ".jpg", ".ifc", ".pdf", ".wasm"}:
            continue  # binary or bulky: path checks only
        try:
            findings += scan_text(rel, path.read_text(encoding="utf-8"))
        except UnicodeDecodeError:
            pass
    return findings


def scan_history() -> list[Finding]:
    """Added lines of every commit on every ref, streamed so the whole history never sits in memory."""
    findings, commit, path, line_no = [], "?", "?", 0
    proc = subprocess.Popen(["git", "log", "-p", "--all", "--no-color", "--no-ext-diff", "-U0"], cwd=ROOT,
                            stdout=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
    for raw in proc.stdout:
        if raw.startswith("commit "):
            commit = raw.split()[1][:10]
        elif raw.startswith("+++ "):
            path = raw[6:].strip() if raw.startswith("+++ b/") else raw[4:].strip()
        elif raw.startswith("@@"):
            m = re.search(r"\+(\d+)", raw)
            line_no = int(m.group(1)) if m else 0
        elif raw.startswith("+") and not raw.startswith("+++"):
            for f in scan_text(path, raw[1:], where=f"history {commit}"):
                f.line = line_no
                findings.append(f)
            line_no += 1
    proc.wait()
    return findings


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    findings = scan_tree()
    if "--no-history" not in argv:
        findings += scan_history()
    for kind in ("secret", "test_placeholder", "personal_path", "file"):
        group = [f for f in findings if f.kind == kind]
        unique = {(f.where.split()[0], f.path, f.snippet): f for f in group}
        print(f"\n== {kind}: {len(group)} finding(s), {len(unique)} distinct")
        for f in list(unique.values())[:60]:
            print(f"  [{f.where}] {f.path}:{f.line}: {f.snippet}")
        if len(unique) > 60:
            print(f"  ... {len(unique) - 60} more")
    secrets = [f for f in findings if f.kind == "secret"]
    print("\nRESULT: " + ("SECRETS FOUND: do not publish" if secrets else "no secrets found") +
          f"; {sum(f.kind == 'personal_path' for f in findings)} personal-path and "
          f"{sum(f.kind == 'file' for f in findings)} file warning(s)")
    return 1 if secrets else 0


if __name__ == "__main__":
    sys.exit(main())
