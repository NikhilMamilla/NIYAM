"""Optional live smoke test: compile all pilot units once, gated, with the hosted model.

Runs only when the hosted LLM is configured in .env (HOSTED_LLM_PROVIDER, HOSTED_LLM_MODEL, and the
key or base URL); otherwise prints "skipped: not configured" and exits 0. Never prints secrets.
Run from backend/ with the venv active:  python ../scripts/live_smoke.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.compiler import cli  # noqa: E402
from app.config import Settings, settings as default_settings  # noqa: E402
from app.llm.base import ProviderNotConfigured  # noqa: E402
from app.llm.factory import get_provider  # noqa: E402


def main(settings: Settings | None = None) -> int:
    try:
        provider = get_provider("hosted", settings or default_settings)
    except ProviderNotConfigured as e:
        print(f"skipped: not configured ({e})")
        return 0
    print(f"live smoke: hosted model {provider.model}, gated, all pilot units")
    return cli.main(["compile-all-pilots", "--role", "hosted"])


if __name__ == "__main__":
    sys.exit(main())
