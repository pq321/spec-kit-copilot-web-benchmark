"""E2E test — run all benchmark scenarios through the full runner."""

from __future__ import annotations

import os
import sys

import pytest

# Allow imports from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from benchmark.runner import run_scenario
from benchmark.scenarios import build_scenario_request_context
from benchmark.types import SCENARIO_EXPECTATIONS
from site.server import start_server


@pytest.fixture(scope="module")
def server() -> dict:
    handle = start_server()
    yield handle
    handle["server"].shutdown()


@pytest.mark.parametrize(
    "scenario,expected",
    [(name, state.value) for name, state in SCENARIO_EXPECTATIONS.items()],
    ids=list(SCENARIO_EXPECTATIONS.keys()),
)
@pytest.mark.asyncio
async def test_scenario(
    tmp_path: str,
    server: dict,
    scenario: str,
    expected: str,
) -> None:
    result = await run_scenario(
        workspace=str(tmp_path),
        scenario=scenario,
        base_url=server["url"],
        request_context=build_scenario_request_context(scenario),
        headless=True,
    )
    assert result["terminalState"] == expected
    assert os.path.exists(result["artifacts"]["state_file"])
