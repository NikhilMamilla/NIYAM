import importlib.util

from app.fixtures.builders import REPO_ROOT

spec = importlib.util.spec_from_file_location("check_public_ready", REPO_ROOT / "scripts" / "check_public_ready.py")
cpr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cpr)

FAKE = "sk-ant-api03-" + "Zx9" * 12  # built at run time so this file itself holds no key-shaped literal


def kinds(text, path="x.py"):
    return [(f.kind, f.line) for f in cpr.scan_text(path, text)]


def test_known_key_prefixes_are_found_and_masked():
    findings = cpr.scan_text("conf.py", f"API = '{FAKE}'\n")
    assert [(f.kind, f.line) for f in findings] == [("secret", 1)]
    assert FAKE not in findings[0].snippet and findings[0].snippet.startswith(FAKE[:4])


def test_high_entropy_values_next_to_secret_words():
    value = "q8Zr2Lm9" + "Xp4Vt7Kc1Nw6Hy3Bd5Fs0Jb"  # built at run time: no secret-shaped literal in this file
    assert kinds(f"token = '{value}'\n") == [("secret", 1)]
    assert kinds("token = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'\n") == []  # low entropy is not a secret
    assert kinds("max_tokens = 4096\napi_key=\n") == []  # placeholders and numbers are fine


def test_private_keys_and_personal_paths():
    assert kinds("-----BEGIN EC " + "PRIVATE KEY-----\n") == [("secret", 1)]
    assert kinds("see C:\\Users" + "\\Anyone\\notes.txt\n") == [("personal_path", 1)]
    assert kinds("open E:/Desk" + "top/x\n") == [("personal_path", 1)]
    assert kinds("C:/Users/<user>/AppData is an example\n") == []  # an explicit placeholder


def test_tracked_file_rules():
    assert cpr.path_problems("backend/data/corpus.db", 10) == ["committed database", "local data (backend/data)"]
    assert cpr.path_problems("node_modules/x/index.js", 10) == ["node_modules"]
    assert cpr.path_problems("eval/runs/x/results.json", 10) == ["run output"]
    assert cpr.path_problems(".env", 10) == ["environment file"]
    assert cpr.path_problems("fixtures/big.ifc", 6 * 1024 * 1024) == ["larger than 5 MB"]
    assert cpr.path_problems(".env.example", 10) == [] and cpr.path_problems("README.md", 10) == []


def test_code_expressions_and_marked_test_keys_are_not_secrets():
    assert kinds("    api_key=s.hosted_llm_api_key, **common)\n") == []
    fake = "sk-test-" + "FAKE" + "0123456789abcdef"
    assert kinds(f"KEY = '{fake}'\n") == [("test_placeholder", 1)]


def test_the_scanners_own_historic_test_inputs_are_recognised_exactly():
    old_token = "q8Zr2Lm9" + "Xp4Vt7Kc1Nw6Hy3Bd5Fs0Ja"  # committed once as a literal in 2fe241c
    own = "backend/tests/test_public_ready.py"
    assert kinds(f"token = '{old_token}'\n", own) == [("test_placeholder", 1)]
    assert kinds("-----BEGIN RSA " + "PRIVATE KEY-----\n", own) == [("test_placeholder", 1)]
    # the same values anywhere else are still secrets: a real RSA key starts with exactly that header
    assert kinds("-----BEGIN RSA " + "PRIVATE KEY-----\n", "deploy/id_rsa") == [("secret", 1)]
    assert kinds(f"token = '{old_token}'\n", "app/settings.py") == [("secret", 1)]
