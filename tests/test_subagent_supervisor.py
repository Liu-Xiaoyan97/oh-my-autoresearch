import json
import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from conftest import REPO_ROOT


SCRIPT = REPO_ROOT / ".claude.template" / "scripts" / "subagent_supervisor.py"


def run_hook(state_root, event, project_dir=None):
    env = os.environ.copy()
    env["AUTORESEARCH_SUPERVISOR_DIR"] = str(state_root)
    if project_dir is not None:
        env["CLAUDE_PROJECT_DIR"] = str(project_dir)
    return subprocess.run(
        ["python3", str(SCRIPT)],
        input=json.dumps(event),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


def run_command(state_root, *args):
    env = os.environ.copy()
    env["AUTORESEARCH_SUPERVISOR_DIR"] = str(state_root)
    return subprocess.run(
        ["python3", str(SCRIPT), *args],
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


def pre_event(role, tool_use_id, transcript="/tmp/agent-parent.jsonl"):
    return {
        "hook_event_name": "PreToolUse",
        "session_id": "session-1",
        "transcript_path": transcript,
        "tool_name": "Agent",
        "tool_use_id": tool_use_id,
        "tool_input": {
            "subagent_type": role,
            "run_in_background": True,
        },
    }


def post_event(role, tool_use_id, agent_id, output_file):
    return {
        "hook_event_name": "PostToolUse",
        "session_id": "session-1",
        "transcript_path": "/tmp/agent-parent.jsonl",
        "tool_name": "Agent",
        "tool_use_id": tool_use_id,
        "tool_input": {
            "subagent_type": role,
            "run_in_background": True,
        },
        "tool_response": {
            "toolUseResult": {
                "agentId": agent_id,
                "outputFile": str(output_file),
            }
        },
    }


def is_denied(result):
    if not result.stdout.strip():
        return False
    payload = json.loads(result.stdout)
    return payload["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_same_role_is_atomically_claimed_once(tmp_path):
    event_a = pre_event("math-theorist", "tool-a")
    event_b = pre_event("math-theorist", "tool-b")

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda event: run_hook(tmp_path, event), [event_a, event_b]))

    assert sum(is_denied(result) for result in results) == 1
    assert sum(not result.stdout.strip() for result in results) == 1


def test_three_distinct_roles_can_launch_in_parallel(tmp_path):
    roles = [
        "flow-arch-reviewer",
        "math-theorist",
        "numerical-debugger",
    ]

    with ThreadPoolExecutor(max_workers=3) as executor:
        results = list(
            executor.map(
                lambda pair: run_hook(tmp_path, pre_event(pair[0], pair[1])),
                [(role, f"tool-{index}") for index, role in enumerate(roles)],
            )
        )

    assert all(result.returncode == 0 for result in results)
    assert all(not result.stdout.strip() for result in results)


def test_reviewer_must_run_in_background(tmp_path):
    event = pre_event("math-theorist", "tool-a")
    event["tool_input"]["run_in_background"] = False

    result = run_hook(tmp_path, event)

    assert is_denied(result)
    assert "run_in_background=true" in result.stdout


def test_stale_agent_can_retry_once_but_not_twice(tmp_path):
    output_file = tmp_path / "agent-output.jsonl"
    output_file.write_text("started\n", encoding="utf-8")
    assert run_hook(tmp_path, pre_event("math-theorist", "tool-a")).returncode == 0
    assert run_hook(
        tmp_path,
        post_event("math-theorist", "tool-a", "agent-1", output_file),
    ).returncode == 0

    old = time.time() - 20
    os.utime(output_file, (old, old))
    record = next(tmp_path.glob("*/*/math-theorist.json"))
    data = json.loads(record.read_text(encoding="utf-8"))
    data["last_heartbeat_epoch"] = old
    record.write_text(json.dumps(data), encoding="utf-8")

    status = run_command(
        tmp_path,
        "status",
        "--agent-id",
        "agent-1",
        "--timeout",
        "1",
    )
    assert json.loads(status.stdout)["status"] == "stale"

    retry = run_command(
        tmp_path,
        "retry",
        "--agent-id",
        "agent-1",
        "--timeout",
        "1",
        "--reason",
        "heartbeat timeout",
    )
    assert retry.returncode == 0

    second = run_hook(tmp_path, pre_event("math-theorist", "tool-b"))
    assert not is_denied(second)

    third = run_hook(tmp_path, pre_event("math-theorist", "tool-c"))
    assert is_denied(third)
    assert "attempt=2" in third.stdout


def test_same_role_is_scoped_to_parent_agent(tmp_path):
    first = run_hook(
        tmp_path,
        pre_event("numerical-debugger", "tool-a", transcript="/tmp/agent-parent-a.jsonl"),
    )
    second = run_hook(
        tmp_path,
        pre_event("numerical-debugger", "tool-b", transcript="/tmp/agent-parent-b.jsonl"),
    )

    assert not is_denied(first)
    assert not is_denied(second)


def test_subagent_stop_completes_wait(tmp_path):
    output_file = tmp_path / "agent-output.jsonl"
    output_file.write_text("done\n", encoding="utf-8")
    assert run_hook(tmp_path, pre_event("flow-arch-reviewer", "tool-a")).returncode == 0
    assert run_hook(
        tmp_path,
        post_event("flow-arch-reviewer", "tool-a", "agent-finished", output_file),
    ).returncode == 0

    stop = {
        "hook_event_name": "SubagentStop",
        "session_id": "session-1",
        "agent_id": "agent-finished",
        "agent_type": "flow-arch-reviewer",
        "last_assistant_message": '{"reviewer_type":"flow-arch-reviewer"}',
    }
    assert run_hook(tmp_path, stop).returncode == 0

    waited = run_command(
        tmp_path,
        "wait",
        "--agent-id",
        "agent-finished",
        "--timeout",
        "1",
        "--poll",
        "1",
    )
    assert waited.returncode == 0
    payload = json.loads(waited.stdout)
    assert payload["agents"][0]["status"] == "completed"


def test_phase9_summarizer_requires_recovery_event_in_queue(tmp_path):
    project = tmp_path / "project"
    events = project / "runtime" / "observer" / "events"
    states = project / "runtime" / "states"
    events.mkdir(parents=True)
    states.mkdir(parents=True)
    (events / "events.jsonl").write_text("", encoding="utf-8")
    (states / "states.json").write_text(
        json.dumps({"exp_name": "exp_9"}),
        encoding="utf-8",
    )
    event = {
        "hook_event_name": "PreToolUse",
        "session_id": "session-1",
        "transcript_path": "/tmp/team-lead.jsonl",
        "tool_name": "Agent",
        "tool_use_id": "summarizer-phase9",
        "tool_input": {
            "subagent_type": "summarizer",
            "prompt": "[phase=9] summarize recovery",
        },
    }

    denied = run_hook(tmp_path / "supervisor", event, project)
    assert is_denied(denied)
    assert "尚未 emit" in denied.stdout

    queued_event = {
        "event_type": "experiments",
        "payload": {
            "action": "mark_complete",
            "exp_name": "exp_9",
            "data": {"recovery_ready": True},
        },
    }
    (events / "events.jsonl").write_text(
        json.dumps(queued_event) + "\n",
        encoding="utf-8",
    )

    allowed = run_hook(tmp_path / "supervisor", event, project)
    assert not is_denied(allowed)
