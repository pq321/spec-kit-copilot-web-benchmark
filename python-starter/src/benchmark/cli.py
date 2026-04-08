"""CLI entry point for running benchmark scenarios."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys

# Allow running from project root without installation
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from benchmark.scenarios import build_scenario_request_context
from benchmark.runner import run_scenario


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a benchmark scenario",
    )
    parser.add_argument(
        "--scenario",
        default="normal",
        help="Scenario name (default: normal)",
    )
    parser.add_argument(
        "--workspace",
        default=os.getcwd(),
        help="Workspace directory for artifacts (default: cwd)",
    )
    parser.add_argument(
        "--headed",
        action="store_true",
        help="Run in headed mode (show browser)",
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help="Base URL of the benchmark site (starts one automatically if omitted)",
    )
    return parser.parse_args(argv)


async def _main(args: argparse.Namespace) -> None:
    workspace = os.path.abspath(args.workspace)
    headless = not args.headed
    base_url = args.base_url

    server_handle = None
    if not base_url:
        from site.server import start_server

        server_handle = start_server()
        base_url = server_handle["url"]

    try:
        result = await run_scenario(
            workspace=workspace,
            scenario=args.scenario,
            base_url=base_url,
            request_context=build_scenario_request_context(args.scenario),
            headless=headless,
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
