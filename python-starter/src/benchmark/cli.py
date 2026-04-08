"""CLI entry point for running benchmark scenarios."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys

# Allow running from source without editable installation.
SRC_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(SRC_ROOT)
for entry in (SRC_ROOT, PROJECT_ROOT):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from benchmark.runner import run_scenario
from benchmark.scenarios import build_scenario_request_context
from benchmark_site.server import start_server


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a benchmark scenario")
    parser.add_argument("--scenario", default="normal", help="Scenario name (default: normal)")
    parser.add_argument("--workspace", default=os.getcwd(), help="Workspace directory for artifacts (default: cwd)")
    parser.add_argument("--headed", action="store_true", help="Run in headed mode (show browser)")
    parser.add_argument("--base-url", default=None, help="Base URL of the benchmark site (starts one automatically if omitted)")
    parser.add_argument(
        "--mode",
        choices=["continuous", "step"],
        default="continuous",
        help="Runtime mode: continuous for the internal baseline, step for resumable bounded actions.",
    )
    parser.add_argument(
        "--decision-source",
        choices=["internal", "ghc"],
        default="internal",
        help="Decision source for the next action.",
    )
    parser.add_argument("--resume", action="store_true", help="Resume the active run from workspace state.")
    parser.add_argument("--run-id", default=None, help="Explicit runId to resume.")
    parser.add_argument("--max-steps", type=int, default=12, help="Maximum number of executed steps for the run.")
    return parser.parse_args(argv)


async def _main(args: argparse.Namespace) -> None:
    workspace = os.path.abspath(args.workspace)
    headless = not args.headed
    base_url = args.base_url
    server_handle = None

    if not base_url:
        server_handle = start_server()
        base_url = server_handle["url"]

    try:
        result = await run_scenario(
            workspace=workspace,
            scenario=args.scenario,
            base_url=base_url,
            request_context=build_scenario_request_context(args.scenario),
            headless=headless,
            max_steps=args.max_steps,
            mode=args.mode,
            decision_source=args.decision_source,
            resume=args.resume,
            run_id=args.run_id,
        )
        print(json.dumps(result, indent=2, default=str))
    finally:
        if server_handle:
            server_handle["server"].shutdown()


def main() -> None:
    args = _parse_args()
    asyncio.run(_main(args))


if __name__ == "__main__":
    main()
