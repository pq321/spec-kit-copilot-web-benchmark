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
    """Supported lifecycle states for a benchmark run."""

    ACTIVE = "active"
    AWAITING_DECISION = "awaiting_decision"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"


RUN_STATE_TRANSITIONS: dict[RunStatus, set[RunStatus]] = {
    RunStatus.ACTIVE: {
        RunStatus.ACTIVE,
        RunStatus.AWAITING_DECISION,
        RunStatus.COMPLETED,
        RunStatus.BLOCKED,
        RunStatus.FAILED,
    },
    RunStatus.AWAITING_DECISION: {
        RunStatus.AWAITING_DECISION,
        RunStatus.ACTIVE,
        RunStatus.COMPLETED,
        RunStatus.BLOCKED,
        RunStatus.FAILED,
    },
    RunStatus.COMPLETED: {RunStatus.COMPLETED},
    RunStatus.BLOCKED: {RunStatus.BLOCKED},
    RunStatus.FAILED: {RunStatus.FAILED},
}


class DecisionSource(str, Enum):
    """Who decides the next action for the benchmark."""

    INTERNAL = "internal"
    GHC = "ghc"


class TerminalState(str, Enum):
    """Terminal benchmark states that map to pass/block/fail outcomes."""

    SUCCESS = "success"
    ALREADY_REQUESTED = "already_requested"
    MANUAL_REVIEW_REQUIRED = "manual_approval_required"
    BLOCKED_BY_VALIDATION = "blocked_by_validation"
    PERMISSION_NOT_AVAILABLE = "permission_not_available"
    UNKNOWN_STATE = "unknown_state"


class ActionType(str, Enum):
    """Actions the runtime can execute."""

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
    """Decision for the next runtime action."""

    state: str = ""
    action_type: ActionType = ActionType.TERMINAL
    reason: str = ""
    terminal: bool = True
    locator: LocatorDescriptor | None = None
    value: str | None = None
    wait_ms: int | None = None
    locator_strategy: str | None = None


@dataclass
class DecisionRequest:
    """Serialized external-decision request for GHC."""

    run_id: str
    step_id: str
    scenario: str
    requested_at: str
    summary: str
    observation: Observation
    request_context: RequestContext
    allowed_action_types: list[str] = field(
        default_factory=lambda: [action.value for action in ActionType]
    )


@dataclass
class DecisionResponse:
    """Serialized external-decision response from GHC."""

    run_id: str
    step_id: str
    action_type: str
    locator: LocatorDescriptor | None = None
    value: str | None = None
    reason: str = ""
    wait_ms: int | None = None
    terminal_state: str | None = None
