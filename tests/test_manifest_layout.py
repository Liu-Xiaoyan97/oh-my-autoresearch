import json
import re

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


def test_settings_do_not_log_tool_noise():
    settings = json.loads((REPO_ROOT / ".claude.template" / "settings.json").read_text(encoding="utf-8"))
    hooks = settings.get("hooks", {})

    assert "PreToolUse" not in hooks
    assert "PostToolUse" not in hooks


def test_registered_agents_are_explicit_and_no_general_purpose():
    allowed = {
        "orthogonal-direction-scout",
        "summarizer",
        "coder",
        "flow-arch-reviewer",
        "math-theorist",
        "numerical-debugger",
    }
    agent_dir = REPO_ROOT / ".claude.template" / "agents"
    registered = set()

    for path in agent_dir.glob("*.md"):
        text = path.read_text(encoding="utf-8")
        match = re.search(r'^name:\s*"([^"]+)"', text, re.MULTILINE)
        assert match, f"{path.name} missing registered name"
        registered.add(match.group(1))

    assert registered == allowed

    team_lead = (REPO_ROOT / ".claude.template" / "CLAUDE.md").read_text(encoding="utf-8")
    assert "严禁使用\n  `general_purpose`" in team_lead
