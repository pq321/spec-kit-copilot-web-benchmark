"""Unit tests for policy.py — decision engine."""

from __future__ import annotations

import pytest

from benchmark.policy import decide_next_action, detect_page_state
from benchmark.types import (
    ActionType,
    LocatorDescriptor,
    Observation,
    RequestContext,
    TerminalState,
)


def _obs(
    *,
    title: str = "",
    headings: list[str] | None = None,
    banners: list[str] | None = None,
    dom_evidence: str = "",
    controls: list[dict] | None = None,
) -> Observation:
    return Observation(
        title=title,
        headings=headings or [],
        banners=banners or [],
        dom_evidence=dom_evidence,
        controls=controls or [],
    )


CTX = RequestContext()


class TestDetectPageState:
    def test_success(self) -> None:
        obs = _obs(dom_evidence="Request submitted successfully!")
        assert detect_page_state(obs) == TerminalState.SUCCESS.value

    def test_already_requested(self) -> None:
        obs = _obs(banners=["Request already exists for this permission."])
        assert detect_page_state(obs) == TerminalState.ALREADY_REQUESTED.value

    def test_manual_review(self) -> None:
        obs = _obs(dom_evidence="Manager approval required before proceeding.")
        assert detect_page_state(obs) == TerminalState.MANUAL_REVIEW_REQUIRED.value

    def test_transient_failure(self) -> None:
        obs = _obs(banners=["Temporary service issue. Please retry."])
        assert detect_page_state(obs) == "transient_failure"

    def test_dynamic_loading(self) -> None:
        obs = _obs(dom_evidence="Unlocking permissions, please wait...")
        assert detect_page_state(obs) == "dynamic_loading"

    def test_step_system(self) -> None:
        obs = _obs(headings=["Step 1: Choose a system"])
        assert detect_page_state(obs) == "step_system"

    def test_step_package(self) -> None:
        obs = _obs(headings=["Step 2: Choose access package"])
        assert detect_page_state(obs) == "step_package"

    def test_step_review(self) -> None:
        obs = _obs(headings=["Step 3: Review request"])
        assert detect_page_state(obs) == "step_review"

    def test_unknown(self) -> None:
        obs = _obs(title="Something completely unexpected")
        assert detect_page_state(obs) == TerminalState.UNKNOWN_STATE.value


class TestDecideNextAction:
    def test_terminal_success(self) -> None:
        obs = _obs(dom_evidence="Request submitted successfully!")
        decision = decide_next_action(CTX, obs)
        assert decision.terminal is True
        assert decision.action_type == ActionType.TERMINAL
        assert decision.state == TerminalState.SUCCESS.value

    def test_terminal_already_requested(self) -> None:
        obs = _obs(banners=["Request already exists"])
        decision = decide_next_action(CTX, obs)
        assert decision.terminal is True
        assert decision.state == TerminalState.ALREADY_REQUESTED.value

    def test_terminal_manual_review(self) -> None:
        obs = _obs(dom_evidence="Manager approval required")
        decision = decide_next_action(CTX, obs)
        assert decision.terminal is True
        assert decision.state == TerminalState.MANUAL_REVIEW_REQUIRED.value

    def test_wait_on_dynamic_loading(self) -> None:
        obs = _obs(dom_evidence="Unlocking permissions...")
        decision = decide_next_action(CTX, obs)
        assert decision.terminal is False
        assert decision.action_type == ActionType.WAIT
        assert decision.wait_ms == 400

    def test_click_retry_on_transient_failure(self) -> None:
        obs = _obs(banners=["Temporary service issue"])
        decision = decide_next_action(CTX, obs)
        assert decision.terminal is False
        assert decision.action_type == ActionType.CLICK
        assert decision.locator is not None
        assert decision.locator.test_id == "submit-request"

    def test_step_system_select(self) -> None:
        obs = _obs(
            headings=["Step 1: Choose a system"],
            controls=[{"role": "combobox", "label": "System", "value": "", "disabled": False}],
        )
        decision = decide_next_action(CTX, obs)
        assert decision.terminal is False
        assert decision.action_type == ActionType.SELECT_OPTION
        assert decision.value == CTX.target_system

    def test_step_system_next(self) -> None:
        obs = _obs(
            headings=["Step 1: Choose a system"],
            controls=[{"role": "combobox", "label": "System", "value": "Payroll Portal", "disabled": False}],
        )
        decision = decide_next_action(CTX, obs)
        assert decision.terminal is False
        assert decision.action_type == ActionType.CLICK
        assert decision.locator is not None
        assert decision.locator.test_id == "workflow-next"

    def test_step_package_select_package(self) -> None:
        obs = _obs(
            headings=["Step 2: Choose access package"],
            controls=[{"role": "combobox", "label": "Access package", "value": "", "disabled": False}],
        )
        decision = decide_next_action(CTX, obs)
        assert decision.action_type == ActionType.SELECT_OPTION
        assert decision.value == CTX.target_package

    def test_step_review_submit(self) -> None:
        obs = _obs(
            headings=["Step 3: Review request"],
            controls=[{"role": "button", "text": "Submit request", "disabled": False}],
        )
        decision = decide_next_action(CTX, obs)
        assert decision.terminal is False
        assert decision.action_type == ActionType.CLICK
        assert decision.locator is not None
        assert decision.locator.test_id == "submit-request"

    def test_step_review_disabled_submit(self) -> None:
        obs = _obs(
            headings=["Step 3: Review request"],
            controls=[{"role": "button", "text": "Submit request", "disabled": True}],
        )
        decision = decide_next_action(CTX, obs)
        assert decision.terminal is True
        assert decision.state == TerminalState.BLOCKED_BY_VALIDATION.value
