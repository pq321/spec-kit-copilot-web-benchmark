"""Scenario runner for continuous and GHC step/resume benchmark modes."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from playwright.async_api import BrowserContext, Page, Playwright, async_playwright

from .browser_adapter import BrowserAdapter
from .observation import capture_observation
from .persistence import (
    consume_decision_response,
    finalize_run,
    load_events,
    load_run,
    record_event,
    start_run,
    write_decision_request,
)
from .policy import decide_next_action, normalize_external_decision
from .types import ActionType, Decision, DecisionSource, Observation, RunStatus, TerminalState


def _map_terminal_to_run_status(terminal_state: str) -> str:
    if terminal_state in (
        TerminalState.SUCCESS.value,
        TerminalState.ALREADY_REQUESTED.value,
    ):
        return RunStatus.COMPLETED.value

    if terminal_state in (
        TerminalState.MANUAL_REVIEW_REQUIRED.value,
        TerminalState.BLOCKED_BY_VALIDATION.value,
        TerminalState.PERMISSION_NOT_AVAILABLE.value,
    ):
        return RunStatus.BLOCKED.value

    return RunStatus.FAILED.value


def _next_step_id(state: dict[str, Any]) -> str:
    return f"S{state['currentStep'] + 1:03d}"


async def _open_runtime(
    *,
    browser_profile_dir: str,
    headless: bool,
) -> tuple[Playwright, BrowserContext, Page, BrowserAdapter]:
    playwright = await async_playwright().start()
    context = await playwright.chromium.launch_persistent_context(
        user_data_dir=browser_profile_dir,
        headless=headless,
    )
    page = context.pages[0] if context.pages else await context.new_page()
    adapter = BrowserAdapter(page)
    return playwright, context, page, adapter


async def _close_runtime(
    playwright: Playwright,
    context: BrowserContext,
    page: Page,
) -> None:
    await page.close()
    await context.close()
    await playwright.stop()


async def _execute_decision(adapter: BrowserAdapter, decision: Decision) -> str | None:
    if decision.action_type == ActionType.SELECT_OPTION:
        return await adapter.select_option(decision.locator, decision.value)  # type: ignore[arg-type]
    if decision.action_type == ActionType.CHECK_BOX:
        return await adapter.check(decision.locator)  # type: ignore[arg-type]
    if decision.action_type == ActionType.CLICK:
        return await adapter.click(decision.locator)  # type: ignore[arg-type]
    if decision.action_type == ActionType.WAIT:
        await adapter.wait_for(decision.wait_ms or 300)
        return "wait"
    return None


async def start_or_resume_run(
    *,
    workspace: str,
    scenario: str,
    request_context: object,
    decision_source: str,
    resume: bool = False,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Create a fresh run or load the active one for the workspace."""
    loaded = await load_run(workspace)
    if resume or run_id:
        if not loaded:
            raise RuntimeError("No active run state exists for --resume.")
        if run_id and loaded["state"]["runId"] != run_id:
            raise RuntimeError("The requested runId does not match the active workspace run.")
        return loaded

    return await start_run(
        workspace=workspace,
        scenario=scenario,
        goal=f"Run controlled benchmark scenario: {scenario}",
        request_context=request_context,
        decision_source=decision_source,
        run_id=run_id,
    )


async def capture_observation_for_turn(
    page: Page,
    adapter: BrowserAdapter,
    *,
    paths: dict[str, str],
    state: dict[str, Any],
) -> tuple[str, Observation]:
    """Capture the current observation for the next step in the run."""
    step_id = _next_step_id(state)
    observation = await capture_observation(
        page,
        adapter,
        screenshot_dir=paths["screenshot_dir"],
        step_id=step_id,
    )
    return step_id, observation


async def execute_one_step(adapter: BrowserAdapter, decision: Decision) -> str | None:
    """Execute a single runtime decision."""
    locator_strategy = await _execute_decision(adapter, decision)
    decision.locator_strategy = locator_strategy
    await adapter.wait_for(150)
    return locator_strategy


async def finalize_terminal_state(
    *,
    paths: dict[str, str],
    state: dict[str, Any],
    scenario: str,
    decision: Decision,
    observation: Observation,
) -> dict[str, Any]:
    """Persist a terminal state and return a standard run result."""
    await record_event(
        paths,
        state=state,
        step_id=_next_step_id(state),
        status=decision.state,
        summary=decision.reason,
        observation=observation,
        decision=decision,
        count_step=False,
    )
    await finalize_run(
        paths,
        state,
        status=_map_terminal_to_run_status(decision.state),
        summary=decision.reason,
        observation=observation,
        next_action={
            "action": "Stop and review the terminal benchmark state.",
            "reason": decision.reason,
            "terminalState": decision.state,
        },
    )
    return {
        "scenario": scenario,
        "runId": state["runId"],
        "terminalState": decision.state,
        "state": state,
        "artifacts": paths,
    }


async def _replay_recorded_steps(
    *,
    adapter: BrowserAdapter,
    paths: dict[str, str],
    state: dict[str, Any],
) -> None:
    """Replay previously executed actions so step-mode can resume deterministically."""
    events = await load_events(paths)
    replayable = [
        event for event in events
        if event.get("status") == "progress" and event.get("decision") and event["stepId"] < _next_step_id(state)
    ]
    for event in replayable:
        payload = event["decision"]
        decision = Decision(
            state=payload["state"],
            action_type=ActionType(payload["action_type"]),
            reason=payload["reason"],
            terminal=payload["terminal"],
            locator=None,
            value=payload.get("value"),
            wait_ms=payload.get("wait_ms"),
            locator_strategy=payload.get("locator_strategy"),
        )
        locator_payload = payload.get("locator")
        if locator_payload:
            from .types import LocatorDescriptor

            decision.locator = LocatorDescriptor(**locator_payload)
        await execute_one_step(adapter, decision)


async def _prepare_runtime_page(
    *,
    adapter: BrowserAdapter,
    base_url: str,
    state: dict[str, Any],
    paths: dict[str, str],
) -> None:
    await adapter.goto_request_page(base_url, state["scenario"])
    if state["currentStep"] > 0:
        await _replay_recorded_steps(adapter=adapter, paths=paths, state=state)


async def run_continuous_mode(
    *,
    workspace: str,
    scenario: str,
    base_url: str,
    request_context: object,
    headless: bool,
    max_steps: int,
    run_id: str | None = None,
    resume: bool = False,
) -> dict[str, Any]:
    """Run the internal baseline mode until a terminal state or step limit."""
    result = await start_or_resume_run(
        workspace=workspace,
        scenario=scenario,
        request_context=request_context,
        decision_source=DecisionSource.INTERNAL.value,
        resume=resume,
        run_id=run_id,
    )
    paths = result["paths"]
    state = result["state"]

    playwright, context, page, adapter = await _open_runtime(
        browser_profile_dir=paths["browser_profile_dir"],
        headless=headless,
    )
    try:
        await _prepare_runtime_page(
            adapter=adapter,
            base_url=base_url,
            state=state,
            paths=paths,
        )

        while state["currentStep"] < max_steps:
            step_id, observation = await capture_observation_for_turn(
                page,
                adapter,
                paths=paths,
                state=state,
            )
            decision = decide_next_action(request_context, observation)  # type: ignore[arg-type]
            if decision.terminal:
                return await finalize_terminal_state(
                    paths=paths,
                    state=state,
                    scenario=scenario,
                    decision=decision,
                    observation=observation,
                )

            await execute_one_step(adapter, decision)
            await record_event(
                paths,
                state=state,
                step_id=step_id,
                status="progress",
                summary=decision.reason,
                observation=observation,
                decision=decision,
            )

        _, observation = await capture_observation_for_turn(
            page,
            adapter,
            paths=paths,
            state=state,
        )
        await finalize_run(
            paths,
            state,
            status=RunStatus.FAILED.value,
            summary="The benchmark exceeded the maximum step limit without reaching a supported terminal state.",
            observation=observation,
            next_action={
                "action": "Inspect the latest observation and update the policy before retrying.",
                "reason": "The run exceeded the maximum step limit.",
                "terminalState": TerminalState.UNKNOWN_STATE.value,
            },
        )
        return {
            "scenario": scenario,
            "runId": state["runId"],
            "terminalState": TerminalState.UNKNOWN_STATE.value,
            "state": state,
            "artifacts": paths,
        }
    finally:
        await _close_runtime(playwright, context, page)


async def run_step_mode(
    *,
    workspace: str,
    scenario: str,
    base_url: str,
    request_context: object,
    headless: bool,
    max_steps: int,
    decision_source: str,
    run_id: str | None = None,
    resume: bool = False,
) -> dict[str, Any]:
    """Run exactly one observation/decision/action loop turn."""
    result = await start_or_resume_run(
        workspace=workspace,
        scenario=scenario,
        request_context=request_context,
        decision_source=decision_source,
        resume=resume,
        run_id=run_id,
    )
    paths = result["paths"]
    state = result["state"]

    if state["currentStep"] >= max_steps:
        raise RuntimeError("The active run has already exceeded the configured max step limit.")

    playwright, context, page, adapter = await _open_runtime(
        browser_profile_dir=paths["browser_profile_dir"],
        headless=headless,
    )
    try:
        await _prepare_runtime_page(
            adapter=adapter,
            base_url=base_url,
            state=state,
            paths=paths,
        )

        if state["status"] == RunStatus.AWAITING_DECISION.value and decision_source == DecisionSource.GHC.value:
            payload = await consume_decision_response(paths, state)
            if payload is None:
                _, observation = await capture_observation_for_turn(
                    page,
                    adapter,
                    paths=paths,
                    state=state,
                )
                await write_decision_request(
                    paths,
                    state,
                    step_id=state["pendingDecisionId"],
                    observation=observation,
                    summary="Still waiting for decision-response.json before the next bounded action can run.",
                )
                return {
                    "scenario": scenario,
                    "runId": state["runId"],
                    "terminalState": None,
                    "state": state,
                    "artifacts": paths,
                }

            decision = normalize_external_decision(
                payload,
                expected_run_id=state["runId"],
                expected_step_id=state["pendingDecisionId"],
            )
            if decision.terminal:
                _, observation = await capture_observation_for_turn(
                    page,
                    adapter,
                    paths=paths,
                    state=state,
                )
                return await finalize_terminal_state(
                    paths=paths,
                    state=state,
                    scenario=scenario,
                    decision=decision,
                    observation=observation,
                )

            await execute_one_step(adapter, decision)
            _, post_action = await capture_observation_for_turn(
                page,
                adapter,
                paths=paths,
                state=state,
            )
            await record_event(
                paths,
                state=state,
                step_id=payload["stepId"],
                status="progress",
                summary=decision.reason,
                observation=post_action,
                decision=decision,
            )
            follow_up = decide_next_action(request_context, post_action)  # type: ignore[arg-type]
            if follow_up.terminal:
                return await finalize_terminal_state(
                    paths=paths,
                    state=state,
                    scenario=scenario,
                    decision=follow_up,
                    observation=post_action,
                )

            next_step_id = _next_step_id(state)
            await write_decision_request(
                paths,
                state,
                step_id=next_step_id,
                observation=post_action,
                summary="One bounded action completed. Review the new observation and choose the next action.",
            )
            return {
                "scenario": scenario,
                "runId": state["runId"],
                "terminalState": None,
                "state": state,
                "artifacts": paths,
            }

        step_id, observation = await capture_observation_for_turn(
            page,
            adapter,
            paths=paths,
            state=state,
        )
        decision = decide_next_action(request_context, observation)  # type: ignore[arg-type]
        if decision.terminal:
            return await finalize_terminal_state(
                paths=paths,
                state=state,
                scenario=scenario,
                decision=decision,
                observation=observation,
            )

        if decision_source == DecisionSource.GHC.value:
            await write_decision_request(
                paths,
                state,
                step_id=step_id,
                observation=observation,
                summary="Observation captured. GHC must supply the next bounded action in decision-response.json.",
            )
            return {
                "scenario": scenario,
                "runId": state["runId"],
                "terminalState": None,
                "state": state,
                "artifacts": paths,
            }

        await execute_one_step(adapter, decision)
        _, post_action = await capture_observation_for_turn(
            page,
            adapter,
            paths=paths,
            state=state,
        )
        await record_event(
            paths,
            state=state,
            step_id=step_id,
            status="progress",
            summary=decision.reason,
            observation=post_action,
            decision=decision,
        )

        follow_up = decide_next_action(request_context, post_action)  # type: ignore[arg-type]
        if follow_up.terminal:
            return await finalize_terminal_state(
                paths=paths,
                state=state,
                scenario=scenario,
                decision=follow_up,
                observation=post_action,
            )

        await finalize_run(
            paths,
            state,
            status=RunStatus.ACTIVE.value,
            summary="One internal step completed. Resume step mode to continue.",
            observation=post_action,
            next_action={
                "action": "Resume step mode to continue the internal baseline loop.",
                "reason": "The last action completed and another supported non-terminal state is available.",
            },
        )
        state["status"] = RunStatus.ACTIVE.value
        return {
            "scenario": scenario,
            "runId": state["runId"],
            "terminalState": None,
            "state": state,
            "artifacts": paths,
        }
    finally:
        await _close_runtime(playwright, context, page)


async def run_scenario(
    *,
    workspace: str,
    scenario: str,
    base_url: str,
    request_context: object,
    headless: bool = True,
    max_steps: int = 12,
    mode: str = "continuous",
    decision_source: str = "internal",
    resume: bool = False,
    run_id: str | None = None,
) -> dict:
    """Run a single benchmark scenario in continuous or step mode."""
    if mode == "continuous" and decision_source != DecisionSource.INTERNAL.value:
        raise ValueError("continuous mode only supports the internal decision source.")

    if mode == "continuous":
        return await run_continuous_mode(
            workspace=workspace,
            scenario=scenario,
            base_url=base_url,
            request_context=request_context,
            headless=headless,
            max_steps=max_steps,
            run_id=run_id,
            resume=resume,
        )

    return await run_step_mode(
        workspace=workspace,
        scenario=scenario,
        base_url=base_url,
        request_context=request_context,
        headless=headless,
        max_steps=max_steps,
        decision_source=decision_source,
        run_id=run_id,
        resume=resume,
    )
