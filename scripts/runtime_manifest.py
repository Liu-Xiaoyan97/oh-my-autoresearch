#!/usr/bin/env python3

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_WORKFLOW = "nn_architecture"


@dataclass(frozen=True)
class RuntimeManifest:
    name: str
    version: str
    runtime_root: str
    copy_if_missing: list[dict[str, str]]
    ensure_dirs: list[str]
    never_overwrite: list[str]
    runtime_required: list[str]
    runtime_generated_patterns: list[str]


class ManifestError(ValueError):
    pass


def repository_root_from_script() -> Path:
    return Path(__file__).resolve().parents[1]


def load_manifest(workflow: str = DEFAULT_WORKFLOW, workflow_root: Path | None = None) -> RuntimeManifest:
    root = workflow_root or repository_root_from_script()
    manifest_path = root / "manifests" / f"{workflow}.yaml"
    if not manifest_path.is_file():
        raise ManifestError(f"Manifest not found: {manifest_path}")

    data = _load_yaml_mapping(manifest_path)
    manifest = RuntimeManifest(
        name=_require_str(data, "name"),
        version=_require_str(data, "version"),
        runtime_root=_require_str(data, "runtime_root"),
        copy_if_missing=_require_list_of_mappings(data, "copy_if_missing"),
        ensure_dirs=_require_list_of_strings(data, "ensure_dirs"),
        never_overwrite=_require_list_of_strings(data, "never_overwrite"),
        runtime_required=_require_list_of_strings(data, "runtime_required"),
        runtime_generated_patterns=_require_list_of_strings(data, "runtime_generated_patterns"),
    )
    _validate_manifest(manifest, root)
    return manifest


def _load_yaml_mapping(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError:
        return _load_simple_manifest_yaml(path)

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ManifestError(f"Manifest must be a mapping: {path}")
    return data


def _load_simple_manifest_yaml(path: Path) -> dict[str, Any]:
    """Parse the small manifest subset used by this repository.

    The fallback intentionally supports only top-level scalars and top-level
    lists of strings or simple mappings. It keeps the scripts dependency-free
    while still failing loudly if the manifest grows beyond this subset.
    """

    data: dict[str, Any] = {}
    current_key: str | None = None
    current_item: dict[str, str] | None = None

    for line_no, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.split("#", 1)[0].rstrip()
        if not line:
            continue

        if not line.startswith(" "):
            if ":" not in line:
                raise ManifestError(f"Invalid manifest line {line_no}: {raw_line}")
            key, value = line.split(":", 1)
            current_key = key.strip()
            current_item = None
            value = value.strip()
            data[current_key] = _strip_quotes(value) if value else []
            continue

        if current_key is None:
            raise ManifestError(f"Indented value without key at line {line_no}: {raw_line}")

        stripped = line.strip()
        if stripped.startswith("- "):
            item = stripped[2:].strip()
            if ":" in item:
                key, value = item.split(":", 1)
                current_item = {key.strip(): _strip_quotes(value.strip())}
                data[current_key].append(current_item)
            else:
                current_item = None
                data[current_key].append(_strip_quotes(item))
            continue

        if current_item is None or ":" not in stripped:
            raise ManifestError(f"Unsupported manifest line {line_no}: {raw_line}")

        key, value = stripped.split(":", 1)
        current_item[key.strip()] = _strip_quotes(value.strip())

    return data


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _require_str(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise ManifestError(f"Manifest key {key!r} must be a non-empty string")
    return value


def _require_list_of_strings(data: dict[str, Any], key: str) -> list[str]:
    value = data.get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ManifestError(f"Manifest key {key!r} must be a list of strings")
    return value


def _require_list_of_mappings(data: dict[str, Any], key: str) -> list[dict[str, str]]:
    value = data.get(key)
    if not isinstance(value, list):
        raise ManifestError(f"Manifest key {key!r} must be a list")

    mappings: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            raise ManifestError(f"Manifest key {key!r} must contain mappings")
        normalized = {str(k): str(v) for k, v in item.items()}
        mappings.append(normalized)
    return mappings


def _validate_manifest(manifest: RuntimeManifest, workflow_root: Path) -> None:
    if manifest.name != DEFAULT_WORKFLOW:
        raise ManifestError(f"Unsupported manifest name: {manifest.name}")

    all_paths = [
        manifest.runtime_root,
        *manifest.ensure_dirs,
        *manifest.never_overwrite,
        *manifest.runtime_required,
    ]
    for entry in manifest.copy_if_missing:
        if set(entry) != {"from", "to"}:
            raise ManifestError(f"copy_if_missing entries must have from/to keys: {entry}")
        all_paths.extend([entry["from"], entry["to"]])
        source = workflow_root / entry["from"]
        if not source.is_file():
            raise ManifestError(f"Template source does not exist: {source}")

    destinations = [entry["to"] for entry in manifest.copy_if_missing]
    duplicates = sorted({path for path in destinations if destinations.count(path) > 1})
    if duplicates:
        raise ManifestError(f"Duplicate copy destinations: {duplicates}")

    for rel_path in all_paths:
        _validate_relative_path(rel_path)


def _validate_relative_path(rel_path: str) -> None:
    path = Path(rel_path)
    if path.is_absolute():
        raise ManifestError(f"Manifest paths must be relative: {rel_path}")
    if any(part == ".." for part in path.parts):
        raise ManifestError(f"Manifest paths must not traverse upward: {rel_path}")
