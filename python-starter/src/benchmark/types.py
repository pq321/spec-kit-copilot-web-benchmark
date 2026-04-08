"""Constants and data models for the benchmark framework."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class LocatorStrategy(str, Enum):
    """Priority order for locator resolution."""

    ROLE = "role"
    LABEL = "label"
    TEXT = "text"
    TEST_ID = "testId"
    CSS = "css"
    XPATH = "xpath"


LOCATOR_STRATEGY_ORDER: list[LocatorStrategy] = [
    LocatorStrategy.ROLE,
    LocatorStrategy.LABEL,
    LocatorStrategy.TEXT,
    LocatorStrategy.TEST_ID,
    LocatorStrategy.CSS,
    LocatorStrategy.XPATH,
]


class RunStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"


class TerminalState(str, Enum):
    SUCCESS = "success"
    ALREADY_REQUESTED = "already_requested"
    MANUAL_REVIEW_REQUIRED = "manual_approval_required"
    BLOCKED_BY_VALIDATION = "blocked_by_validation"
    UNKNOWN_STATE = "unknown_state"


class ActionType(str, Enum):
    SELECT_OPTION = "select_option"
    CHECK_BOX = "check_box"
    CLICK = "click"
    WAIT = "wait"
    TERMINAL = "terminal"


SCENARIO_EXPECTATIONS: dict[str, TerminalState] = {
    "normal": TerminalState.SUCCESS,
    "already_requested": TerminalState.ALREADY_REQUESTED,
    "prerequisite_unlock": TerminalState.SUCCESS,
    "ambiguous_locator": TerminalState.SUCCESS,
    "dynamic_dom": TerminalState.SUCCESS,
    "manual_review": TerminalState.MANUAL_REVIEW_REQUIRED,
    "failure_recovery": TerminalState.SUCCESS,
}


@dataclass
class LocatorDescriptor:
    """Describes how to find an element on the page."""

    scope: str | None = None
    role: str | None = None
    name: str | None = None
    label: str | None = None
    text: str | None = None
    test_id: str | None = None
    css: str | None = None
    xpath: str | None = None


@dataclass
class RequestContext:
    """Context for a benchmark scenario run."""

    scenario: str = "normal"
    target_system: str = "Payroll Portal"
    target_package: str = "Finance Reporter"
    target_permission: str = "View Reports"
    account_name: str = "benchmark.user@example.com"
    environment: str = "benchmark"
    approval_mode: str = "auto-when-possible"


@dataclass
class Observation:
    """Captured page state."""

    url: str = ""
    title: str = ""
    headings: list[str] = field(default_factory=list)
    banners: list[str] = field(default_factory=list)
    dom_evidence: str = ""
    screenshot_path: str = ""
    controls: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class Decision:
    """Policy decision for the next action."""

    state: str = ""
    action_type: ActionType = ActionType.TERMINAL
    reason: str = ""
    terminal: bool = True
    locator: LocatorDescriptor | None = None
    value: str | None = None
    wait_ms: int | None = None
    locator_strategy: str | None = None
