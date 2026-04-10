"""Template synchronization helpers for git-restricted environments."""

from .core import SyncResult, apply_sync, bootstrap_manifest, load_manifest

__all__ = ["SyncResult", "apply_sync", "bootstrap_manifest", "load_manifest"]
