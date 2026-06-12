#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from runtime_manifest import DEFAULT_WORKFLOW, ManifestError, load_manifest, repository_root_from_script


ALLOWED_PHASES = {"A", "B", "C", "D", "E", "F", "BLOCKED", "DONE"}
ALLOWED_WORKFLOW_STATUS = {"running", "blocked", "done"}
ALLOWED_LOCAL_VALIDATION_STATUS = {"not_started", "passed", "failed", "skipped"}
ALLOWED_REMOTE_TRAINING_STATUS = {"not_started", "queued", "running", "succeeded", "failed", "cancelled"}
ALLOWED_RESULT_STATUS = {"pending", "succeeded", "failed", "cancelled"}
ALLOWED_VAL_LOSS_STATUS = {"queued", "running", "succeeded", "failed", "cancelled"}
ALLOWED_AGENTTEAM_STATUS = {"not_started", "in_progress", "complete", "blocked", "skipped"}
B1_B3_F2_AGENTS = ["math-theorist", "numerical-debugger", "flow-arch-reviewer"]
B2_AGENT = "orthogonal-direction-scout"


def load_json(path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"Missing JSON file: {path}")
        return {}
    except json.JSONDecodeError as exc:
        errors.append(f"Invalid JSON: {path}: {exc}")
        return {}

    if not isinstance(data, dict):
        errors.append(f"JSON root must be an object: {path}")
        return {}
    return data


def validate_runtime(
    root: Path,
    workflow: str = DEFAULT_WORKFLOW,
    workflow_root: Path | None = None,
) -> list[str]:
    runtime_root = root.resolve()
    repo_root = workflow_root or repository_root_from_script()
    errors: list[str] = []

    try:
        manifest = load_manifest(workflow=workflow, workflow_root=repo_root)
    except ManifestError as exc:
        return [str(exc)]

    for rel_dir in manifest.ensure_dirs:
        if not (runtime_root / rel_dir).is_dir():
            errors.append(f"Missing required directory: {rel_dir}")

    for rel_file in manifest.runtime_required:
        if not (runtime_root / rel_file).is_file():
            errors.append(f"Missing required file: {rel_file}")

    if errors:
        return errors

    objective = _load_objective(runtime_root / "runtime/objective/objective.yaml", errors)
    state = validate_state(runtime_root, errors)
    current_iteration = validate_current_iteration(runtime_root, errors)
    val_loss = validate_val_loss(runtime_root, errors)
    validate_timeline(runtime_root, errors)
    best = validate_best(runtime_root, errors)
    validate_cross_file_consistency(objective, state, current_iteration, val_loss, best, errors)
    return errors


def _load_objective(path: Path, errors: list[str]) -> dict[str, Any]:
    if not path.is_file():
        errors.append(f"Missing objective file: {path}")
        return {}

    text = path.read_text(encoding="utf-8")
    top_level_keys = _top_level_yaml_keys(text)
    required = {
        "goal",
        "primary_metric",
        "success_criteria",
        "stop_conditions",
        "constraints",
        "exploration_policy",
    }
    missing = sorted(required - top_level_keys)
    if missing:
        errors.append(f"{path} missing top-level keys: {missing}")

    if "name: val_loss" not in text:
        errors.append(f"{path} primary_metric.name must be val_loss")
    if "mode: minimize" not in text:
        errors.append(f"{path} primary_metric.mode must be minimize")

    return {"keys": top_level_keys, "text": text}


def _top_level_yaml_keys(text: str) -> set[str]:
    keys: set[str] = set()
    for raw_line in text.splitlines():
        if not raw_line or raw_line.startswith((" ", "\t", "#")):
            continue
        if ":" in raw_line:
            keys.add(raw_line.split(":", 1)[0].strip())
    return keys


def validate_state(root: Path, errors: list[str]) -> dict[str, Any]:
    path = root / "runtime/state/state.json"
    data = load_json(path, errors)
    if not data:
        return data

    _require_keys(
        data,
        path,
        ["workflow_status", "phase", "phase_step", "iteration", "current_exp_name", "next_phase", "blocked"],
        errors,
    )

    phase = data.get("phase")
    if phase not in ALLOWED_PHASES:
        errors.append(f"{path} phase must be one of {sorted(ALLOWED_PHASES)}")

    next_phase = data.get("next_phase")
    if next_phase is not None and next_phase not in ALLOWED_PHASES:
        errors.append(f"{path} next_phase must be null or one of {sorted(ALLOWED_PHASES)}")

    workflow_status = data.get("workflow_status")
    if workflow_status not in ALLOWED_WORKFLOW_STATUS:
        errors.append(f"{path} workflow_status must be one of {sorted(ALLOWED_WORKFLOW_STATUS)}")

    if not isinstance(data.get("iteration"), int) or data.get("iteration", -1) < 0:
        errors.append(f"{path} iteration must be a non-negative integer")

    if not isinstance(data.get("blocked"), bool):
        errors.append(f"{path} blocked must be a boolean")

    if data.get("blocked") and phase != "BLOCKED":
        errors.append(f"{path} blocked=true requires phase=BLOCKED")

    if phase == "BLOCKED" and workflow_status != "blocked":
        errors.append(f"{path} phase=BLOCKED requires workflow_status=blocked")

    if phase == "DONE" and workflow_status != "done":
        errors.append(f"{path} phase=DONE requires workflow_status=done")

    if phase in {"A", "B", "C", "D", "E", "F"}:
        phase_step = data.get("phase_step")
        if not isinstance(phase_step, str) or not phase_step.startswith(phase):
            errors.append(f"{path} phase_step must start with current phase {phase!r}")

    if data.get("blocked") and not data.get("block_reason"):
        errors.append(f"{path} blocked=true requires a non-empty block_reason")

    return data


def validate_current_iteration(root: Path, errors: list[str]) -> dict[str, Any]:
    path = root / "runtime/state/current_iteration.json"
    data = load_json(path, errors)
    if not data:
        return data

    _require_keys(data, path, ["exp_name", "iteration", "local_validation", "remote_training", "result"], errors)

    if not isinstance(data.get("iteration"), int) or data.get("iteration", -1) < 0:
        errors.append(f"{path} iteration must be a non-negative integer")

    for key in ["candidate_directions", "deduplicated_directions"]:
        if key in data and not isinstance(data[key], list):
            errors.append(f"{path} {key} must be a list")

    if "agentteam" in data:
        validate_agentteam(data["agentteam"], path, errors)

    local_validation = _require_object(data, "local_validation", path, errors)
    _require_keys(local_validation, path, ["status", "commands", "passed", "notes"], errors, prefix="local_validation.")
    if local_validation.get("status") not in ALLOWED_LOCAL_VALIDATION_STATUS:
        errors.append(f"{path} local_validation.status must be one of {sorted(ALLOWED_LOCAL_VALIDATION_STATUS)}")
    if not isinstance(local_validation.get("commands"), list):
        errors.append(f"{path} local_validation.commands must be a list")
    if not isinstance(local_validation.get("passed"), bool):
        errors.append(f"{path} local_validation.passed must be a boolean")
    if not isinstance(local_validation.get("notes"), list):
        errors.append(f"{path} local_validation.notes must be a list")
    if local_validation.get("status") == "passed" and local_validation.get("passed") is not True:
        errors.append(f"{path} local_validation.status=passed requires passed=true")
    if local_validation.get("status") == "failed" and local_validation.get("passed") is not False:
        errors.append(f"{path} local_validation.status=failed requires passed=false")

    remote_training = _require_object(data, "remote_training", path, errors)
    _require_keys(remote_training, path, ["status"], errors, prefix="remote_training.")
    if remote_training.get("status") not in ALLOWED_REMOTE_TRAINING_STATUS:
        errors.append(f"{path} remote_training.status must be one of {sorted(ALLOWED_REMOTE_TRAINING_STATUS)}")

    result = _require_object(data, "result", path, errors)
    _require_keys(result, path, ["status", "best_val_loss", "final_val_loss", "best_epoch", "is_new_best"], errors, prefix="result.")
    if result.get("status") not in ALLOWED_RESULT_STATUS:
        errors.append(f"{path} result.status must be one of {sorted(ALLOWED_RESULT_STATUS)}")
    if not isinstance(result.get("is_new_best"), bool):
        errors.append(f"{path} result.is_new_best must be a boolean")
    for key in ["best_val_loss", "final_val_loss"]:
        if result.get(key) is not None and not _is_number(result[key]):
            errors.append(f"{path} result.{key} must be a number or null")
    if result.get("best_epoch") is not None and not isinstance(result.get("best_epoch"), int):
        errors.append(f"{path} result.best_epoch must be an integer or null")

    return data


def validate_agentteam(value: Any, path: Path, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{path} agentteam must be an object")
        return

    required_sections = [
        "b1_candidate_review",
        "b2_orthogonality_review",
        "b3_plan_selection",
        "f2_evidence_review",
    ]
    _require_keys(value, path, required_sections, errors, prefix="agentteam.")

    b1 = _optional_object(value, "b1_candidate_review", path, errors)
    if b1:
        _validate_agentteam_status(b1, "agentteam.b1_candidate_review", path, errors)
        _validate_exact_agents(b1.get("agents"), B1_B3_F2_AGENTS, "agentteam.b1_candidate_review.agents", path, errors)
        if not isinstance(b1.get("candidate_count"), int) or b1.get("candidate_count", -1) < 0:
            errors.append(f"{path} agentteam.b1_candidate_review.candidate_count must be a non-negative integer")
        if not isinstance(b1.get("blocking_issues"), list):
            errors.append(f"{path} agentteam.b1_candidate_review.blocking_issues must be a list")

    b2 = _optional_object(value, "b2_orthogonality_review", path, errors)
    if b2:
        _validate_agentteam_status(b2, "agentteam.b2_orthogonality_review", path, errors)
        if b2.get("agent") != B2_AGENT:
            errors.append(f"{path} agentteam.b2_orthogonality_review.agent must be {B2_AGENT}")
        for key in ["accepted_candidates", "rejected_candidates"]:
            if not isinstance(b2.get(key), list):
                errors.append(f"{path} agentteam.b2_orthogonality_review.{key} must be a list")

    b3 = _optional_object(value, "b3_plan_selection", path, errors)
    if b3:
        _validate_agentteam_status(b3, "agentteam.b3_plan_selection", path, errors)
        _validate_exact_agents(b3.get("agents"), B1_B3_F2_AGENTS, "agentteam.b3_plan_selection.agents", path, errors)
        for key in ["implementation_risks", "diagnostic_requirements"]:
            if not isinstance(b3.get(key), list):
                errors.append(f"{path} agentteam.b3_plan_selection.{key} must be a list")

    f2 = _optional_object(value, "f2_evidence_review", path, errors)
    if f2:
        _validate_agentteam_status(f2, "agentteam.f2_evidence_review", path, errors)
        _validate_exact_agents(f2.get("agents"), B1_B3_F2_AGENTS, "agentteam.f2_evidence_review.agents", path, errors)
        if f2.get("verdict") not in {"learned", "rejected", "inconclusive", None}:
            errors.append(f"{path} agentteam.f2_evidence_review.verdict must be learned, rejected, inconclusive, or null")
        if not isinstance(f2.get("missing_evidence"), list):
            errors.append(f"{path} agentteam.f2_evidence_review.missing_evidence must be a list")


def _optional_object(data: dict[str, Any], key: str, path: Path, errors: list[str]) -> dict[str, Any]:
    value = data.get(key)
    if value is None:
        return {}
    if not isinstance(value, dict):
        errors.append(f"{path} agentteam.{key} must be an object")
        return {}
    return value


def _validate_agentteam_status(data: dict[str, Any], prefix: str, path: Path, errors: list[str]) -> None:
    if data.get("status") not in ALLOWED_AGENTTEAM_STATUS:
        errors.append(f"{path} {prefix}.status must be one of {sorted(ALLOWED_AGENTTEAM_STATUS)}")


def _validate_exact_agents(value: Any, expected: list[str], prefix: str, path: Path, errors: list[str]) -> None:
    if value != expected:
        errors.append(f"{path} {prefix} must be exactly {expected}")


def validate_val_loss(root: Path, errors: list[str]) -> dict[str, Any]:
    path = root / "runtime/state/val_loss.json"
    data = load_json(path, errors)
    if not data:
        return data

    if data.get("metric") != "val_loss":
        errors.append(f"{path} metric must be val_loss")
    if data.get("mode") != "minimize":
        errors.append(f"{path} mode must be minimize")

    records = data.get("records")
    if not isinstance(records, list):
        errors.append(f"{path} records must be a list")
        return data

    seen: set[tuple[str, int]] = set()
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append(f"{path} record #{index} must be an object")
            continue
        _require_keys(record, path, ["exp_name", "iteration", "best_val_loss", "final_val_loss", "best_epoch", "status"], errors, prefix=f"records[{index}].")
        exp_name = record.get("exp_name")
        iteration = record.get("iteration")
        if not isinstance(exp_name, str) or not exp_name:
            errors.append(f"{path} records[{index}].exp_name must be a non-empty string")
        if not isinstance(iteration, int) or iteration < 0:
            errors.append(f"{path} records[{index}].iteration must be a non-negative integer")
        if record.get("status") not in ALLOWED_VAL_LOSS_STATUS:
            errors.append(f"{path} records[{index}].status must be one of {sorted(ALLOWED_VAL_LOSS_STATUS)}")
        if isinstance(exp_name, str) and isinstance(iteration, int):
            key = (exp_name, iteration)
            if key in seen:
                errors.append(f"{path} duplicate val_loss record for {exp_name} iteration {iteration}")
            seen.add(key)
        for loss_key in ["best_val_loss", "final_val_loss"]:
            if record.get(loss_key) is not None and not _is_number(record[loss_key]):
                errors.append(f"{path} records[{index}].{loss_key} must be a number or null")
        if record.get("best_epoch") is not None and not isinstance(record.get("best_epoch"), int):
            errors.append(f"{path} records[{index}].best_epoch must be an integer or null")

    return data


def validate_timeline(root: Path, errors: list[str]) -> dict[str, Any]:
    path = root / "runtime/history/timeline.json"
    data = load_json(path, errors)
    if not data:
        return data

    events = data.get("events")
    if not isinstance(events, list):
        errors.append(f"{path} events must be a list")
        return data

    for index, event in enumerate(events):
        if not isinstance(event, dict):
            errors.append(f"{path} events[{index}] must be an object")
            continue
        _require_keys(event, path, ["time", "iteration", "exp_name", "event_type", "summary"], errors, prefix=f"events[{index}].")
        if not isinstance(event.get("iteration"), int) or event.get("iteration", -1) < 0:
            errors.append(f"{path} events[{index}].iteration must be a non-negative integer")
        if not isinstance(event.get("summary"), str) or not event.get("summary"):
            errors.append(f"{path} events[{index}].summary must be a non-empty string")

    return data


def validate_best(root: Path, errors: list[str]) -> dict[str, Any]:
    path = root / "runtime/experiments/best.json"
    data = load_json(path, errors)
    if not data:
        return data

    if data.get("metric") != "val_loss":
        errors.append(f"{path} metric must be val_loss")
    if data.get("mode") != "minimize":
        errors.append(f"{path} mode must be minimize")
    if "best" not in data:
        errors.append(f"{path} missing best")
        return data

    best = data.get("best")
    if best is None:
        return data
    if not isinstance(best, dict):
        errors.append(f"{path} best must be an object or null")
        return data

    _require_keys(best, path, ["exp_name", "iteration", "best_val_loss"], errors, prefix="best.")
    if not isinstance(best.get("exp_name"), str) or not best.get("exp_name"):
        errors.append(f"{path} best.exp_name must be a non-empty string")
    if not isinstance(best.get("iteration"), int) or best.get("iteration", -1) < 0:
        errors.append(f"{path} best.iteration must be a non-negative integer")
    if not _is_number(best.get("best_val_loss")):
        errors.append(f"{path} best.best_val_loss must be a number")

    return data


def validate_cross_file_consistency(
    objective: dict[str, Any],
    state: dict[str, Any],
    current_iteration: dict[str, Any],
    val_loss: dict[str, Any],
    best: dict[str, Any],
    errors: list[str],
) -> None:
    if state and current_iteration:
        if state.get("iteration") != current_iteration.get("iteration"):
            errors.append("state.json iteration must match current_iteration.json iteration")
        if state.get("current_exp_name") != current_iteration.get("exp_name"):
            errors.append("state.json current_exp_name must match current_iteration.json exp_name")

    if not objective:
        return

    best_record = best.get("best") if isinstance(best.get("best"), dict) else None
    records = val_loss.get("records") if isinstance(val_loss.get("records"), list) else []
    if best_record and records:
        matching = [
            record
            for record in records
            if isinstance(record, dict)
            and record.get("exp_name") == best_record.get("exp_name")
            and record.get("iteration") == best_record.get("iteration")
        ]
        if not matching:
            errors.append("best.json best experiment must also exist in val_loss.json records")


def _require_object(data: dict[str, Any], key: str, path: Path, errors: list[str]) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        errors.append(f"{path} {key} must be an object")
        return {}
    return value


def _require_keys(
    data: dict[str, Any],
    path: Path,
    keys: list[str],
    errors: list[str],
    prefix: str = "",
) -> None:
    for key in keys:
        if key not in data:
            errors.append(f"{path} missing {prefix}{key}")


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a research-runtime repository.")
    parser.add_argument("--root", default=".", help="Path to the research-runtime repository root.")
    parser.add_argument("--workflow", default=DEFAULT_WORKFLOW, help="Workflow manifest name.")
    parser.add_argument(
        "--workflow-root",
        default=None,
        help="Path to the oh-my-autoresearch repository. Defaults to this script's repository.",
    )
    args = parser.parse_args()

    workflow_root = Path(args.workflow_root).resolve() if args.workflow_root else None
    errors = validate_runtime(Path(args.root), workflow=args.workflow, workflow_root=workflow_root)
    if errors:
        print("Runtime validation failed.", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Runtime validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
