"""Pytest configuration for source-tree imports."""

from __future__ import annotations

import os
import sys


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_ROOT = os.path.join(PROJECT_ROOT, "src")

for entry in (PROJECT_ROOT, SRC_ROOT):
    if entry not in sys.path:
        sys.path.insert(0, entry)
