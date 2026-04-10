"""CLI for syncing the starter template without git pull."""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
import zipfile
from pathlib import Path
from urllib.request import urlopen

from .core import SyncResult, apply_sync, bootstrap_manifest, collect_tree, load_manifest


DEFAULT_SOURCE_URI = (
    "https://github.com/pq321/spec-kit-copilot-web-benchmark/archive/refs/heads/main.zip"
)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync the GHC template without git.")
    parser.add_argument(
        "mode",
        choices=["bootstrap", "sync"],
        help="bootstrap creates the local manifest; sync applies remote changes safely.",
    )
    parser.add_argument("--workspace", default=".", help="Local project directory to sync.")
    parser.add_argument(
        "--source-uri",
        default=DEFAULT_SOURCE_URI,
        help="Zip archive URL for the remote template.",
    )
    parser.add_argument(
        "--source-zip-path",
        default=None,
        help="Local zip archive path. Overrides --source-uri when provided.",
    )
    parser.add_argument(
        "--remote-subdir",
        default="python-starter",
        help="Subdirectory inside the archive that contains the template.",
    )
    parser.add_argument(
        "--archive-root-prefix",
        default="spec-kit-copilot-web-benchmark-main",
        help="Top-level extracted archive folder name.",
    )
    parser.add_argument(
        "--state-dir-name",
        default=".template-sync",
        help="Directory used to store sync metadata and conflicts.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON output.",
    )
    return parser.parse_args(argv)


def _download_or_locate_zip(args: argparse.Namespace, temp_dir: Path) -> Path:
    if args.source_zip_path:
        return Path(args.source_zip_path).resolve()
    zip_path = temp_dir / "template-source.zip"
    with urlopen(args.source_uri) as response, zip_path.open("wb") as handle:
        handle.write(response.read())
    return zip_path


def _extract_source_root(args: argparse.Namespace, zip_path: Path, temp_dir: Path) -> Path:
    extract_root = temp_dir / "source"
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(extract_root)
    return extract_root / args.archive_root_prefix / args.remote_subdir


def _result_payload(result: SyncResult | None, manifest_only: bool, manifest_path: Path) -> dict:
    payload = {
        "mode": "bootstrap" if manifest_only else "sync",
        "manifestPath": str(manifest_path),
    }
    if result is not None:
        payload.update(result.to_dict())
    return payload


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    workspace = Path(args.workspace).resolve()
    workspace.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="template-sync-") as temp_name:
        temp_dir = Path(temp_name)
        zip_path = _download_or_locate_zip(args, temp_dir)
        source_root = _extract_source_root(args, zip_path, temp_dir)
        if not source_root.exists():
            raise FileNotFoundError(f"Template subdirectory not found in archive: {source_root}")

        if args.mode == "bootstrap":
            remote_tree = collect_tree(source_root)
            manifest = bootstrap_manifest(
                workspace=workspace,
                remote_tree=remote_tree,
                source_uri=None if args.source_zip_path else args.source_uri,
                remote_subdir=args.remote_subdir,
                state_dir_name=args.state_dir_name,
                existing_manifest=load_manifest(workspace, state_dir_name=args.state_dir_name),
            )
            payload = _result_payload(
                result=None,
                manifest_only=True,
                manifest_path=workspace / args.state_dir_name / "manifest.json",
            )
            payload["trackedFileCount"] = len(manifest["trackedFiles"])
        else:
            result = apply_sync(
                workspace=workspace,
                source_root=source_root,
                source_uri=None if args.source_zip_path else args.source_uri,
                remote_subdir=args.remote_subdir,
                state_dir_name=args.state_dir_name,
            )
            payload = _result_payload(
                result=result,
                manifest_only=False,
                manifest_path=workspace / args.state_dir_name / "manifest.json",
            )

    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
