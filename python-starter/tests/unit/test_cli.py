"""Unit tests for the CLI argument surface."""

from __future__ import annotations

from benchmark.cli import _parse_args


def test_parse_args_defaults() -> None:
    args = _parse_args([])
    assert args.mode == "continuous"
    assert args.decision_source == "internal"
    assert args.resume is False
    assert args.run_id is None
    assert args.max_steps == 12


def test_parse_args_step_mode() -> None:
    args = _parse_args([
        "--mode",
        "step",
        "--decision-source",
        "ghc",
        "--resume",
        "--run-id",
        "run-fixed",
        "--max-steps",
        "4",
    ])
    assert args.mode == "step"
    assert args.decision_source == "ghc"
    assert args.resume is True
    assert args.run_id == "run-fixed"
    assert args.max_steps == 4
