# Geometric gate (generated Python checks)

A geometric rule unit (tier `geometric`) is a small Python function written by an LLM or a person:

```python
import math

def check(model, helpers):      # exactly this signature
    ...
    return [helpers.finding(element, "pass" | "fail" | "unchecked", "plain sentence", measured, required), ...]
```

`helpers` (`backend/app/geometry/helpers.py`) returns SI values (metres, m²) or `None`; a helper never guesses.
Elements the check does not return a finding for are reported `out_of_scope` by the audit.

## Length units

Every helper returns metres and square metres whatever the project length unit. `ifcopenshell.geom` already
converts geometry to SI, so `_mesh` does not scale it again; declared quantities (`declared_quantity`) are stored in
project units and are converted there. Until branch fix-mm-units `_mesh` did scale again, and the fixture builder
wrote millimetre shapes 1000x too large, so the two cancelled on the fixtures while real millimetre models came out
10^6 too small in area: see `STATUS.md`. `backend/tests/test_length_units.py` checks the helpers against IFC files
written by hand, not by the fixture builder.

## What the gate checks (`app/verifier/geometric_gate.py`, `python -m app.verifier.cli check-geo <unit> <file>`)

Stops at the first failing stage. Failure messages go through the same masking as the IDS gate.

| # | Stage | Rejects |
|---|---|---|
| 1 | `python_syntax` | code that does not parse, or is longer than 8 KB |
| 2 | `ast_allowlist` | see below |
| 3 | `sandbox_load` | the check cannot run in the isolated process: timeout, crash, exception, oversize output |
| 4 | `returns_findings` | anything but a list of well-formed finding dicts |
| 5 | `applicable_on_fixtures` | no pass or fail finding in the pass fixture or in the fail fixture (a vacuous check) |
| 6 | `verdict_pass_fixture` | any `fail` on the compliant fixture |
| 7 | `verdict_fail_fixture` | no `fail` on the non-compliant fixture, or failing elements other than the expected ones |
| 8 | `no_unchecked_on_clean_fixtures` | any `unchecked` on the fixtures (their data is complete: the check is hiding behind unchecked) |

### AST allowlist (stage 2), as implemented

Rejected with the construct and line number:

- any import except a plain `import math` at the top of the file (`from ... import`, aliases, nested imports);
- any top-level statement except `import math`, a docstring and exactly one function named `check` with exactly
  the parameters `(model, helpers)` (no defaults, `*args`, keyword-only parameters or decorators);
- the names or attributes `open exec eval compile __import__ getattr setattr delattr globals locals vars
  breakpoint input os sys subprocess socket pathlib shutil ctypes importlib builtins type dir memoryview help
  exit quit`;
- any name or attribute that starts and ends with `__` (so `().__class__`, `__subclasses__`, `__globals__`);
- `.format` / `.format_map` (they can walk attributes from a format string, which the dunder scan cannot see);
  f-strings are allowed because their expressions are ordinary AST nodes and are scanned;
- class definitions, async functions, `global`/`nonlocal`, `await`, generators, `del`, `with`, `try`.

Loops and comprehensions are allowed. A `while` over unbounded input is not rejected statically: the timeout
covers it.

### Sandbox (stage 3 and the audit)

The code runs only in a separate process (`app/verifier/sandbox.py` → `sandbox_runner.py`):

- **Enforced:** a separate `python -I` interpreter (no user site, no `PYTHON*` variables); an environment built
  from an allowlist (`PATH`, `SYSTEMROOT`, temp dirs, …) from which anything named `KEY`, `TOKEN`, `SECRET` or
  `PASSWORD` is removed again; a fresh empty temporary working directory; a wall-clock timeout (default 20 s in
  the gate, 60 s in the audit) after which the process is killed; a cap on the JSON it may return (1 MB); a
  restricted `__builtins__` (no `open`, `eval`, `type`, `getattr`, …; `__import__` only allows `math`); stdout
  of the check is discarded so it cannot forge the result line.
- **Not enforced (Windows is the development OS, the `resource` module is not used):** memory or CPU limits,
  file-system access outside the working directory (the process runs as the same user), network access, and
  the number of child processes. The child receives the real `ifcopenshell` model and helper functions, so code
  that finds a Python object-graph escape the AST scan misses could still reach the interpreter.

**This is defence in depth, not a hard security boundary.** The rules are:

1. Generated code is only ever run through this gate or through `sandbox.run_check` after `validate_source`.
2. A human must review any Python in the rulepack before it is used outside the sandbox. All rulepack Python is
   currently a **draft, not human-reviewed**.
3. Run the audit service of untrusted rulepacks inside a container or VM if you need a real boundary.

## What the model sees

The compiler prompt contains the role, the helper API (generated from `helpers.py`), the check contract, the
modelling profile and synthetic examples (guard-rail height). It never contains fixtures, gold checks or their
element names. Repair messages are masked like the IDS gate's: file names, element names and GlobalIds become
"the compliant model", "the element that must FAIL", "a control element that must PASS". Stage messages never
include measured values from the fixtures.
