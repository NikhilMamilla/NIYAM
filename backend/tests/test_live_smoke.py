import importlib.util

from app.config import REPO_ROOT, Settings


def load_script():
    spec = importlib.util.spec_from_file_location("live_smoke", REPO_ROOT / "scripts" / "live_smoke.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_live_smoke_skips_cleanly_when_not_configured(capsys):
    code = load_script().main(Settings(_env_file=None))
    assert code == 0
    assert "skipped: not configured" in capsys.readouterr().out
