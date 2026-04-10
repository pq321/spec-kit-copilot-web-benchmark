"""Tests for safe template sync without git pull."""

from __future__ import annotations

import json
from pathlib import Path

from template_sync.core import apply_sync, bootstrap_manifest, collect_tree, load_manifest


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_bootstrap_manifest_records_remote_tree(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    remote = tmp_path / "remote"
    workspace.mkdir()
    _write(remote / "README.md", "remote-readme")
    _write(remote / "src" / "main.py", "print('hi')\n")

    manifest = bootstrap_manifest(
        workspace=workspace,
        remote_tree=collect_tree(remote),
        source_uri="https://example.test/template.zip",
        remote_subdir="python-starter",
    )

    saved = load_manifest(workspace)
    assert saved is not None
    assert saved["source"]["sourceUri"] == "https://example.test/template.zip"
    assert set(saved["trackedFiles"]) == {"README.md", "src/main.py"}
    assert len(manifest["trackedFiles"]) == 2


def test_sync_updates_untouched_file(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    remote_v1 = tmp_path / "remote-v1"
    remote_v2 = tmp_path / "remote-v2"
    workspace.mkdir()
    _write(remote_v1 / "README.md", "v1")
    _write(remote_v2 / "README.md", "v2")
    _write(workspace / "README.md", "v1")

    bootstrap_manifest(
        workspace=workspace,
        remote_tree=collect_tree(remote_v1),
        source_uri="https://example.test/template.zip",
        remote_subdir="python-starter",
    )
    result = apply_sync(
        workspace=workspace,
        source_root=remote_v2,
        source_uri="https://example.test/template.zip",
        remote_subdir="python-starter",
    )

    assert result.updated == ["README.md"]
    assert (workspace / "README.md").read_text(encoding="utf-8") == "v2"


def test_sync_preserves_local_modification_when_remote_unchanged(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    remote = tmp_path / "remote"
    workspace.mkdir()
    _write(remote / "README.md", "template-v1")
    _write(workspace / "README.md", "local-change")

    bootstrap_manifest(
        workspace=workspace,
        remote_tree=collect_tree(remote),
        source_uri="https://example.test/template.zip",
        remote_subdir="python-starter",
    )

    result = apply_sync(
        workspace=workspace,
        source_root=remote,
        source_uri="https://example.test/template.zip",
        remote_subdir="python-starter",
    )

    assert result.preserved_local == ["README.md"]
    assert (workspace / "README.md").read_text(encoding="utf-8") == "local-change"


def test_sync_writes_conflict_copy_when_both_sides_changed(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    remote_v1 = tmp_path / "remote-v1"
    remote_v2 = tmp_path / "remote-v2"
    workspace.mkdir()
    _write(remote_v1 / "README.md", "v1")
    _write(remote_v2 / "README.md", "remote-v2")
    _write(workspace / "README.md", "local-v2")

    bootstrap_manifest(
        workspace=workspace,
        remote_tree=collect_tree(remote_v1),
        source_uri="https://example.test/template.zip",
        remote_subdir="python-starter",
    )

    result = apply_sync(
        workspace=workspace,
        source_root=remote_v2,
        source_uri="https://example.test/template.zip",
        remote_subdir="python-starter",
    )

    conflict_copy = workspace / ".template-sync" / "conflicts" / "README.md.remote"
    assert result.conflicts == ["README.md"]
    assert conflict_copy.read_text(encoding="utf-8") == "remote-v2"
    assert (workspace / "README.md").read_text(encoding="utf-8") == "local-v2"


def test_sync_deletes_untouched_removed_remote_file(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    remote_v1 = tmp_path / "remote-v1"
    remote_v2 = tmp_path / "remote-v2"
    workspace.mkdir()
    _write(remote_v1 / "README.md", "v1")
    _write(workspace / "README.md", "v1")
    remote_v2.mkdir()

    bootstrap_manifest(
        workspace=workspace,
        remote_tree=collect_tree(remote_v1),
        source_uri="https://example.test/template.zip",
        remote_subdir="python-starter",
    )

    result = apply_sync(
        workspace=workspace,
        source_root=remote_v2,
        source_uri="https://example.test/template.zip",
        remote_subdir="python-starter",
    )

    assert result.deleted == ["README.md"]
    assert not (workspace / "README.md").exists()


def test_sync_requires_manifest_before_merge(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    remote = tmp_path / "remote"
    workspace.mkdir()
    _write(remote / "README.md", "v1")

    try:
        apply_sync(
            workspace=workspace,
            source_root=remote,
            source_uri="https://example.test/template.zip",
            remote_subdir="python-starter",
        )
    except RuntimeError as exc:
        assert "bootstrap" in str(exc)
    else:
        raise AssertionError("Expected apply_sync to require a manifest.")
