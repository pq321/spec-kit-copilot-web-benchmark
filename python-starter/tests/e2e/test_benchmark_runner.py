"""E2E tests for continuous and step-mode benchmark execution."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict

import pytest

# Allow imports from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from benchmark.policy import decide_next_action
from benchmark.runner import run_scenario
from benchmark.scenarios import build_scenario_request_context
from benchmark.types import Observation, RequestContext, SCENARIO_EXPECTATIONS
from benchmark_site.server import start_server


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
async def test_continuous_scenario(
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


def _read_json(path: str) -> dict:
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _build_decision_response(workspace: str) -> dict:
    request = _read_json(os.path.join(workspace, ".copilot-agent-kit", "queue", "decision-request.json"))
    state = _read_json(os.path.join(workspace, ".copilot-agent-kit", "state", "run-state.json"))

    observation = Observation(**request["observation"])
    context = RequestContext(**state["requestContext"])
    decision = decide_next_action(context, observation)

    return {
        "runId": request["runId"],
        "stepId": request["stepId"],
        "actionType": decision.action_type.value,
        "locator": asdict(decision.locator) if decision.locator else None,
        "value": decision.value,
        "reason": decision.reason,
    }


async def _drive_ghc_step_loop(tmp_path: str, server: dict, scenario: str) -> dict:
    request_context = build_scenario_request_context(scenario)
    result = await run_scenario(
        workspace=str(tmp_path),
        scenario=scenario,
        base_url=server["url"],
        request_context=request_context,
        headless=True,
        mode="step",
        decision_source="ghc",
        max_steps=12,
    )

    state_path = os.path.join(tmp_path, ".copilot-agent-kit", "state", "run-state.json")
    first_state = _read_json(state_path)
    run_id = first_state["runId"]
    browser_profile_dir = first_state["browserProfileDir"]
    assert result["state"]["status"] == "awaiting_decision"

    for _ in range(12):
        response = _build_decision_response(str(tmp_path))
        response_path = os.path.join(tmp_path, ".copilot-agent-kit", "queue", "decision-response.json")
        with open(response_path, "w", encoding="utf-8") as handle:
            json.dump(response, handle, indent=2)
            handle.write("\n")

        result = await run_scenario(
            workspace=str(tmp_path),
            scenario=scenario,
            base_url=server["url"],
            request_context=request_context,
            headless=True,
            mode="step",
            decision_source="ghc",
            resume=True,
            run_id=run_id,
            max_steps=12,
        )

        current_state = _read_json(state_path)
        assert current_state["runId"] == run_id
        assert current_state["browserProfileDir"] == browser_profile_dir

        if current_state["status"] in {"completed", "blocked", "failed"}:
            return result

    raise AssertionError(f"Step loop for {scenario} did not reach a terminal state.")


@pytest.mark.asyncio
async def test_step_mode_waits_for_external_decision(tmp_path: str, server: dict) -> None:
    request_context = build_scenario_request_context("normal")
    await run_scenario(
        workspace=str(tmp_path),
        scenario="normal",
        base_url=server["url"],
        request_context=request_context,
        headless=True,
        mode="step",
        decision_source="ghc",
        max_steps=12,
    )

    state_path = os.path.join(tmp_path, ".copilot-agent-kit", "state", "run-state.json")
    state_before = _read_json(state_path)
    request_file = os.path.join(tmp_path, ".copilot-agent-kit", "queue", "decision-request.json")
    assert os.path.exists(request_file)
    assert state_before["status"] == "awaiting_decision"
    assert state_before["currentStep"] == 0

    await run_scenario(
        workspace=str(tmp_path),
        scenario="normal",
        base_url=server["url"],
        request_context=request_context,
        headless=True,
        mode="step",
        decision_source="ghc",
        resume=True,
        run_id=state_before["runId"],
        max_steps=12,
    )

    state_after = _read_json(state_path)
    assert state_after["status"] == "awaiting_decision"
    assert state_after["currentStep"] == 0
    assert state_after["pendingDecisionId"] == state_before["pendingDecisionId"]


@pytest.mark.parametrize(
    "scenario,expected",
    [
        ("normal", "success"),
        ("already_requested", "already_requested"),
        ("prerequisite_unlock", "success"),
        ("manual_review", "manual_approval_required"),
    ],
)
@pytest.mark.asyncio
async def test_step_mode_external_loop_reaches_terminal_state(
    tmp_path: str,
    server: dict,
    scenario: str,
    expected: str,
) -> None:
    result = await _drive_ghc_step_loop(tmp_path, server, scenario)
    state = _read_json(os.path.join(tmp_path, ".copilot-agent-kit", "state", "run-state.json"))
    next_action = _read_json(os.path.join(tmp_path, ".copilot-agent-kit", "queue", "next-action.json"))

    assert result["terminalState"] == expected
    assert state["terminalState"] == expected
    assert state["status"] in {"completed", "blocked"}
    assert state["currentStep"] >= 1 or scenario == "already_requested"
    assert next_action["terminalState"] == expected
