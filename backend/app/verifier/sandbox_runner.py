"""Runs one generated check in an isolated child process (`python -I`). Not importable API: see sandbox.py.

argv: <backend dir> <max output bytes> <ifc path>...      stdin: the check's source code
The last line of stdout is MARKER + JSON ({"ok": true, "results": [...]} or {"ok": false, "error": "..."})."""

import json
import math
import os
import sys

MARKER = "@@NIYAM-RESULT@@"
ALLOWED_BUILTINS = (
    "abs all any bool dict enumerate filter float int isinstance len list map max min range reversed round set "
    "sorted str sum tuple zip ValueError TypeError KeyError IndexError ZeroDivisionError Exception"
).split()


def _safe_import(name, globals=None, locals=None, fromlist=(), level=0):
    if name != "math" or fromlist or level:
        raise ImportError(f"import of {name!r} is not allowed")
    return math


def _builtins() -> dict:
    import builtins

    table = {n: getattr(builtins, n) for n in ALLOWED_BUILTINS}
    table.update({"True": True, "False": False, "None": None, "__import__": _safe_import})
    return table


def main() -> None:
    backend, max_bytes, *paths = sys.argv[1:]
    code = sys.stdin.read()
    real_stdout, sys.stdout = sys.stdout, open(os.devnull, "w")  # nothing the check prints can forge the result
    try:
        sys.path.insert(0, backend)
        import ifcopenshell

        from app.geometry.helpers import HELPERS

        namespace = {"__builtins__": _builtins(), "__name__": "niyam_check"}
        exec(compile(code, "<check>", "exec"), namespace)
        check = namespace.get("check")
        if not callable(check):
            raise TypeError("the code does not define check")
        result = {"ok": True, "results": [check(ifcopenshell.open(p), HELPERS) for p in paths]}
        payload = json.dumps(result, default=repr)
        if len(payload) > int(max_bytes):
            payload = json.dumps({"ok": False, "error": f"output of {len(payload)} bytes exceeds the {max_bytes} byte cap"})
    except BaseException as e:  # noqa: BLE001 - everything the untrusted code can raise is reported, not crashed on
        payload = json.dumps({"ok": False, "error": f"{type(e).__name__}: {e}"[:2000]})
    real_stdout.write("\n" + MARKER + payload + "\n")
    real_stdout.flush()


if __name__ == "__main__":
    main()
