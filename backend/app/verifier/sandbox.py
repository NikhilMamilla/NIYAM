"""Run generated geometric checks in a separate, isolated process.

This is defence in depth, NOT a hard security boundary (see docs/geometric-gate.md). Enforced here: a separate
`python -I` process, a scrubbed environment (an allowlist, with anything named KEY/TOKEN/SECRET/PASSWORD removed
again), a fresh temporary working directory, a wall-clock timeout that kills the process, and a cap on the size of
the JSON it may return. Not enforced on Windows: memory, CPU or file-system/network access limits."""

import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from app.verifier.sandbox_runner import MARKER

BACKEND_DIR = Path(__file__).resolve().parents[2]
RUNNER = Path(__file__).with_name("sandbox_runner.py")
SECRETISH = re.compile(r"KEY|TOKEN|SECRET|PASSWORD", re.IGNORECASE)
KEEP_ENV = {"SYSTEMROOT", "WINDIR", "PATH", "PATHEXT", "COMSPEC", "TEMP", "TMP", "LANG", "LC_ALL"}
DEFAULT_TIMEOUT_S = 20.0
DEFAULT_MAX_OUTPUT_BYTES = 1_000_000


@dataclass
class SandboxOutcome:
    ok: bool
    results: list | None = None  # one list of raw finding dicts per model path
    error: str | None = None
    kind: str | None = None  # "timeout" | "output" | "crash" | "error" when not ok


# numpy's BLAS allocates buffers per CPU thread; several sandboxes at once ran out of memory ("OpenBLAS error:
# Memory allocation still failed") on a loaded machine. The checks do no linear algebra, so one thread is enough.
SINGLE_THREAD = {"OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"}


def scrubbed_env(source=None) -> dict[str, str]:
    source = os.environ if source is None else source
    kept = {k: v for k, v in source.items() if k.upper() in KEEP_ENV and not SECRETISH.search(k)}
    return kept | SINGLE_THREAD


def _spawn(args: list[str], stdin: str, timeout_s: float):
    with tempfile.TemporaryDirectory(prefix="niyam-sandbox-") as cwd:
        return subprocess.run([sys.executable, "-I", *args], input=stdin, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=timeout_s, cwd=cwd, env=scrubbed_env())


def run_check(code: str, ifc_paths, *, timeout_s: float = DEFAULT_TIMEOUT_S,
              max_output_bytes: int = DEFAULT_MAX_OUTPUT_BYTES) -> SandboxOutcome:
    """Execute `code` (already AST-validated) against each model in its own process and return the raw findings."""
    # the child runs in a fresh temporary directory, so every path it is given must be absolute
    args = [str(RUNNER), str(BACKEND_DIR), str(max_output_bytes), *(str(Path(p).resolve()) for p in ifc_paths)]
    try:
        done = _spawn(args, code, timeout_s)
    except subprocess.TimeoutExpired:
        return SandboxOutcome(False, error=f"the check timed out after {timeout_s:g} s", kind="timeout")
    lines = [ln for ln in done.stdout.splitlines() if ln.startswith(MARKER)]
    if not lines:
        tail = " ".join(done.stderr.split())[-300:]
        return SandboxOutcome(False, error=f"the check process ended without a result (exit {done.returncode}): {tail}",
                              kind="crash")
    if len(lines[-1]) > max_output_bytes + len(MARKER) + 200:
        return SandboxOutcome(False, error="the check's output exceeds the size cap", kind="output")
    payload = json.loads(lines[-1][len(MARKER):])
    if not payload["ok"]:
        kind = "output" if "exceeds" in payload["error"] else "error"
        return SandboxOutcome(False, error=payload["error"], kind=kind)
    return SandboxOutcome(True, results=payload["results"])


def probe_environment() -> dict:
    """What an isolated child process sees (used by tests to show secrets and the cwd are not inherited)."""
    snippet = "import json, os, sys; print(json.dumps({'env': dict(os.environ), 'cwd': os.getcwd(), " \
              "'isolated': bool(sys.flags.isolated)}))"
    done = _spawn(["-c", snippet], "", 30.0)
    return json.loads(done.stdout)
