"""Main scenario runner — orchestrates browser, observation, and policy."""

from __future__ import annotations

import json

from playwright.async_api import async_playwright

from .browser_adapter import BrowserAdapter
from .observation import capture_observation
from .persistence import finalize_run, record_event, start_run
from .policy import decide_next_action
from .types import ActionType, Decision, RunStatus, TerminalState


async def _execute_decision(adapter: BrowserAdapter, decision: Decision) -> str | None:
    """Execute a policy decision and return the locator strategy used."""
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


def _map_terminal_to_run_status(terminal_state: str) -> str:
    if terminal_state in (
        TerminalState.SUCCESS.value,
        TerminalState.ALREADY_REQUESTED.value,
    ):
        return RunStatus.COMPLETED.value

    if terminal_state in (
        TerminalState.MANUAL_REVIEW_REQUIRED.value,
        TerminalState.BLOCKED_BY_VALIDATION.value,
    ):
        return RunStatus.BLOCKED.value

    return RunStatus.FAILED.value


async def run_scenario(
    *,
    workspace: str,
    scenario: str,
    base_url: str,
    request_context: object,
    headless: bool = True,
    max_steps: int = 12,
) -> dict:
    """Run a single benchmark scenario end-to-end."""
    result = await start_run(
        workspace=workspace,
        scenario=scenario,
        goal=f"Run controlled benchmark scenario: {scenario}",
        request_context=request_context,
    )
    paths = result["paths"]
    state = result["state"]

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=headless)
        page = await browser.new_page()
        adapter = BrowserAdapter(page)

        try:
            await adapter.goto_request_page(base_url, scenario)

            for step_index in range(1, max_steps + 1):
                step_id = f"S{step_index:03d}"
                observation = await capture_observation(
                    page, adapter, screenshot_dir=paths["screenshot_dir"], step_id=step_id,
                )
                decision = decide_next_action(request_context, observation)  # type: ignore[arg-type]

                if decision.terminal:
                    await record_event(
                        paths,
                        state=state,
                        step_id=step_id,
                        status=decision.state,
                        summary=decision.reason,
                        observation=observation,
                        decision=decision,
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
                        "terminalState": decision.state,
                        "state": state,
                        "artifacts": paths,
                    }

                locator_strategy = await _execute_decision(adapter, decision)
                decision.locator_strategy = locator_strategy
                await adapter.wait_for(150)

                await record_event(
                    paths,
                    state=state,
                    step_id=step_id,
                    status="progress",
                    summary=decision.reason,
                    observation=observation,
                    decision=decision,
                )

            # Exceeded max steps
            observation = await capture_observation(
                page, adapter, screenshot_dir=paths["screenshot_dir"], step_id="S999",
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
                "terminalState": TerminalState.UNKNOWN_STATE.value,
                "state": state,
                "artifacts": paths,
            }
        finally:
            await page.close()
            await browser.close()
