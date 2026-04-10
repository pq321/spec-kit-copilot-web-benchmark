"""Safe template sync logic for projects that cannot use git pull."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


MANIFEST_VERSION = 1


@dataclass
class SyncResult:
    """Structured sync outcome for reporting and tests."""

    added: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    deleted: list[str] = field(default_factory=list)
    preserved_local: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "added": self.added,
            "updated": self.updated,
            "deleted": self.deleted,
            "preservedLocal": self.preserved_local,
            "conflicts": self.conflicts,
            "warnings": self.warnings,
        }


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def file_hash(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _relative_key(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def collect_tree(root: Path, *, ignore_dirs: set[str] | None = None) -> dict[str, str]:
    """Return relative path -> sha256 for all files under root."""
    ignore = ignore_dirs or set()
    result: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in ignore for part in path.parts):
            continue
        result[_relative_key(path, root)] = file_hash(path)
    return result


def _state_paths(workspace: Path, state_dir_name: str) -> dict[str, Path]:
    state_root = workspace / state_dir_name
    return {
        "root": state_root,
        "manifest": state_root / "manifest.json",
        "report": state_root / "last-sync-report.json",
        "conflicts": state_root / "conflicts",
        "downloads": state_root / "downloads",
    }


def load_manifest(workspace: Path, *, state_dir_name: str = ".template-sync") -> dict[str, Any] | None:
    """Load the current sync manifest if present."""
    manifest_path = _state_paths(workspace, state_dir_name)["manifest"]
    if not manifest_path.exists():
        return None
    with manifest_path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def bootstrap_manifest(
    *,
    workspace: Path,
    remote_tree: dict[str, str],
    source_uri: str | None,
    remote_subdir: str,
    state_dir_name: str = ".template-sync",
    existing_manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Record the current remote template version as the local sync baseline."""
    manifest = {
        "version": MANIFEST_VERSION,
        "source": {
            "sourceUri": source_uri,
            "remoteSubdir": remote_subdir,
        },
        "trackedFiles": {path: {"syncedHash": file_hash_value} for path, file_hash_value in remote_tree.items()},
    }
    if existing_manifest and "source" in existing_manifest:
        manifest["source"].update({k: v for k, v in existing_manifest["source"].items() if v and not manifest["source"].get(k)})
    _write_json(_state_paths(workspace, state_dir_name)["manifest"], manifest)
    return manifest


def _copy_file(source_root: Path, target_root: Path, relative_path: str) -> None:
    destination = target_root / relative_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_root / relative_path, destination)


def _delete_file(target_root: Path, relative_path: str) -> None:
    destination = target_root / relative_path
    if destination.exists():
        destination.unlink()
        parent = destination.parent
        while parent != target_root and parent.exists() and not any(parent.iterdir()):
            parent.rmdir()
            parent = parent.parent


def _write_conflict_copy(
    *,
    state_paths: dict[str, Path],
    source_root: Path,
    relative_path: str,
) -> None:
    remote_copy = state_paths["conflicts"] / f"{relative_path}.remote"
    remote_copy.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_root / relative_path, remote_copy)


def apply_sync(
    *,
    workspace: Path,
    source_root: Path,
    source_uri: str | None,
    remote_subdir: str,
    state_dir_name: str = ".template-sync",
) -> SyncResult:
    """Apply a safe file-level sync from source_root into workspace."""
    state_paths = _state_paths(workspace, state_dir_name)
    state_paths["root"].mkdir(parents=True, exist_ok=True)
    state_paths["conflicts"].mkdir(parents=True, exist_ok=True)

    remote_tree = collect_tree(source_root)
    local_manifest = load_manifest(workspace, state_dir_name=state_dir_name)
    if local_manifest is None:
        raise RuntimeError(
            "No sync manifest found. Run bootstrap first so local modifications can be tracked safely."
        )

    tracked = local_manifest.get("trackedFiles", {})
    result = SyncResult()

    # Handle files that exist remotely.
    for relative_path, remote_hash in remote_tree.items():
        tracked_entry = tracked.get(relative_path)
        previous_hash = tracked_entry["syncedHash"] if tracked_entry else None
        local_file = workspace / relative_path
        local_exists = local_file.exists()
        local_hash = file_hash(local_file) if local_exists else None

        if previous_hash is None:
            if not local_exists:
                _copy_file(source_root, workspace, relative_path)
                result.added.append(relative_path)
            elif local_hash == remote_hash:
                result.preserved_local.append(relative_path)
            else:
                _write_conflict_copy(
                    state_paths=state_paths,
                    source_root=source_root,
                    relative_path=relative_path,
                )
                result.conflicts.append(relative_path)
            tracked[relative_path] = {"syncedHash": remote_hash}
            continue

        if not local_exists:
            if remote_hash == previous_hash:
                result.preserved_local.append(relative_path)
                continue
            _write_conflict_copy(
                state_paths=state_paths,
                source_root=source_root,
                relative_path=relative_path,
            )
            result.conflicts.append(relative_path)
            continue

        if local_hash == previous_hash:
            if remote_hash != previous_hash:
                _copy_file(source_root, workspace, relative_path)
                result.updated.append(relative_path)
            tracked[relative_path] = {"syncedHash": remote_hash}
            continue

        if local_hash == remote_hash:
            tracked[relative_path] = {"syncedHash": remote_hash}
            result.preserved_local.append(relative_path)
            continue

        if remote_hash == previous_hash:
            result.preserved_local.append(relative_path)
            continue

        _write_conflict_copy(
            state_paths=state_paths,
            source_root=source_root,
            relative_path=relative_path,
        )
        result.conflicts.append(relative_path)

    # Handle files that were removed remotely.
    for relative_path, tracked_entry in list(tracked.items()):
        if relative_path in remote_tree:
            continue
        previous_hash = tracked_entry["syncedHash"]
        local_file = workspace / relative_path
        if local_file.exists():
            local_hash = file_hash(local_file)
            if local_hash == previous_hash:
                _delete_file(workspace, relative_path)
                result.deleted.append(relative_path)
            else:
                result.conflicts.append(relative_path)
        tracked.pop(relative_path, None)

    manifest = {
        "version": MANIFEST_VERSION,
        "source": {
            "sourceUri": source_uri,
            "remoteSubdir": remote_subdir,
        },
        "trackedFiles": tracked,
    }
    _write_json(state_paths["manifest"], manifest)
    _write_json(state_paths["report"], result.to_dict())
    return result
