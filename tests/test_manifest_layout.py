import json

from conftest import REPO_ROOT


def test_manifest_declared_files_exist():
    manifest = json.loads((REPO_ROOT / "manifest.json").read_text(encoding="utf-8"))

    for section in ("claude_template", "runtime_template"):
        source = REPO_ROOT / manifest[section]["source"]
        missing = [path for path in manifest[section]["files"] if not (source / path).exists()]

        assert missing == []


def test_forbidden_layouts_are_absent():
    forbidden = [
        REPO_ROOT / ".claude.template" / "agents" / "team-lead.md",
        REPO_ROOT / ".claude.template" / "agents" / "observer.md",
        REPO_ROOT / "runtime.template" / "team-lead",
        REPO_ROOT / "runtime.template" / "artifacts",
        REPO_ROOT / "runtime.template" / "observer" / "agents",
        REPO_ROOT / "src",
        REPO_ROOT / "migrations",
    ]

    assert [str(path.relative_to(REPO_ROOT)) for path in forbidden if path.exists()] == []
