"""Benchmark scenario definitions."""

from __future__ import annotations

from dataclasses import dataclass

from .types import SCENARIO_EXPECTATIONS, RequestContext


@dataclass(frozen=True)
class Scenario:
    name: str
    expected_terminal_state: str


BENCHMARK_SCENARIOS: list[Scenario] = [
    Scenario(name=name, expected_terminal_state=state.value)
    for name, state in SCENARIO_EXPECTATIONS.items()
]


def build_scenario_request_context(
    scenario: str, **overrides: object,
) -> RequestContext:
    kwargs: dict = {"scenario": scenario, **overrides}
    return RequestContext(**kwargs)
