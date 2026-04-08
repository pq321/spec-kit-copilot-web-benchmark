"""Benchmark framework — Python port of the JS benchmark suite."""

from .types import (
    ActionType,
    LocatorDescriptor,
    LocatorStrategy,
    LOCATOR_STRATEGY_ORDER,
    Observation,
    RequestContext,
    RunStatus,
    TerminalState,
    SCENARIO_EXPECTATIONS,
)
from .scenarios import BENCHMARK_SCENARIOS, build_scenario_request_context
from .browser_adapter import BrowserAdapter, build_locator_plan
from .observation import capture_observation
from .policy import decide_next_action, detect_page_state
from .persistence import (
    finalize_run,
    load_events,
    record_event,
    resolve_artifact_paths,
    start_run,
)
from .runner import run_scenario

__all__ = [
    "ActionType",
    "BENCHMARK_SCENARIOS",
    "BrowserAdapter",
    "LOCATOR_STRATEGY_ORDER",
    "LocatorDescriptor",
    "LocatorStrategy",
    "Observation",
    "RequestContext",
    "RunStatus",
    "SCENARIO_EXPECTATIONS",
    "TerminalState",
    "build_locator_plan",
    "build_scenario_request_context",
    "capture_observation",
    "decide_next_action",
    "detect_page_state",
    "finalize_run",
    "load_events",
    "record_event",
    "resolve_artifact_paths",
    "run_scenario",
    "start_run",
]
