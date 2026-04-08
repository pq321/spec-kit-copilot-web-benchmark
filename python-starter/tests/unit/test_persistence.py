"""Unit tests for persistence.py file-based run state and events."""

from __future__ import annotations

import json
import os

import pytest

from benchmark.persistence import (
    consume_decision_response,
    finalize_run,
    load_run,
    load_events,
    record_event,
    resolve_artifact_paths,
    start_run,
    write_decision_request,
)
from benchmark.types import Observation, RequestContext, RunStatus


@pytest.fixture
def workspace(tmp_path: object) -> str:
    return str(tmp_path)


@pytest.fixture
def ctx() -> RequestContext:
    return RequestContext(scenario="normal")


@pytest.mark.asyncio
async def test_start_run_creates_files(workspace: str, ctx: RequestContext) -> None:
    result = await start_run(
        workspace=workspace,
        scenario="normal",
        goal="test goal",
        request_context=ctx,
        decision_source="ghc",
        run_id="run-fixed",
    )
    paths = result["paths"]
    state = result["state"]

    assert os.path.exists(paths["state_file"])
    assert os.path.exists(paths["next_action_file"])
    assert os.path.exists(paths["summary_file"])
    assert paths["browser_profile_dir"].endswith(os.path.join("browser", "run-fixed"))

    with open(paths["state_file"], encoding="utf-8") as handle:
        saved = json.load(handle)
    assert saved["runId"] == "run-fixed"
    assert saved["decisionSource"] == "ghc"
    assert saved["scenario"] == "normal"
    assert saved["status"] == RunStatus.ACTIVE.value
    assert saved["currentStep"] == 0
    assert saved["stepsRecorded"] == 0
    assert saved["browserProfileDir"].endswith(os.path.join("browser", "run-fixed"))
    assert saved["pendingDecisionId"] is None
    assert saved["terminalState"] is None
    assert state["runId"] == "run-fixed"


@pytest.mark.asyncio
async def test_record_event_appends(workspace: str, ctx: RequestContext) -> None:
    result = await start_run(
        workspace=workspace,
        scenario="normal",
        goal="test",
        request_context=ctx,
    )
    paths = result["paths"]
    state = result["state"]

    await record_event(
        paths,
        state=state,
        step_id="S001",
        status="progress",
        summary="Test step",
        observation=None,
        decision=None,
    )

    events = await load_events(paths)
    assert len(events) == 1
    assert events[0]["stepId"] == "S001"
    assert events[0]["summary"] == "Test step"
    assert state["stepsRecorded"] == 1
    assert state["currentStep"] == 1


@pytest.mark.asyncio
async def test_write_decision_request_sets_awaiting_decision(workspace: str, ctx: RequestContext) -> None:
    result = await start_run(
        workspace=workspace,
        scenario="normal",
        goal="test",
        request_context=ctx,
        decision_source="ghc",
        run_id="run-fixed",
    )
    paths = result["paths"]
    state = result["state"]

    observation = Observation(
        url="http://example.test/request.html?scenario=normal",
        title="Permission Request Workflow",
        headings=["Step 1: Choose a system"],
        banners=["Complete the workflow one step at a time."],
        dom_evidence="Step 1: Choose a system",
        screenshot_path="screens/S001.png",
        controls=[{"role": "combobox", "label": "System", "value": "", "disabled": False}],
    )

    await write_decision_request(
        paths,
        state,
        step_id="S001",
        observation=observation,
        summary="Need an external decision for the current page.",
    )

    with open(paths["state_file"], encoding="utf-8") as handle:
        saved_state = json.load(handle)
    with open(paths["decision_request_file"], encoding="utf-8") as handle:
        request = json.load(handle)

    assert saved_state["status"] == RunStatus.AWAITING_DECISION.value
    assert saved_state["pendingDecisionId"] == "S001"
    assert saved_state["lastPageUrl"] == observation.url
    assert request["runId"] == "run-fixed"
    assert request["stepId"] == "S001"
    assert request["observation"]["title"] == observation.title
    assert request["observation"]["controls"][0]["label"] == "System"


@pytest.mark.asyncio
async def test_consume_decision_response_reads_and_clears_file(workspace: str, ctx: RequestContext) -> None:
    result = await start_run(
        workspace=workspace,
        scenario="normal",
        goal="test",
        request_context=ctx,
        decision_source="ghc",
        run_id="run-fixed",
    )
    paths = result["paths"]
    state = result["state"]
    state["pendingDecisionId"] = "S001"
    state["status"] = RunStatus.AWAITING_DECISION.value

    with open(paths["state_file"], "w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2)
        handle.write("\n")

    payload = {
        "runId": "run-fixed",
        "stepId": "S001",
        "actionType": "click",
        "locator": {"label": "System"},
        "value": None,
        "reason": "Continue the workflow.",
    }
    with open(paths["decision_response_file"], "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")

    response = await consume_decision_response(paths, state)
    assert response == payload
    assert not os.path.exists(paths["decision_response_file"])


@pytest.mark.asyncio
async def test_finalize_run(workspace: str, ctx: RequestContext) -> None:
    result = await start_run(
        workspace=workspace,
        scenario="normal",
        goal="test",
        request_context=ctx,
    )
    paths = result["paths"]
    state = result["state"]
    state["pendingDecisionId"] = "S009"

    await finalize_run(
        paths,
        state,
        status=RunStatus.COMPLETED.value,
        summary="All done",
        observation=None,
        next_action={
            "action": "Stop.",
            "reason": "Done.",
            "terminalState": "success",
        },
    )

    with open(paths["state_file"], encoding="utf-8") as handle:
        saved = json.load(handle)
    assert saved["status"] == RunStatus.COMPLETED.value
    assert saved["lastSummary"] == "All done"
    assert saved["terminalState"] == "success"
    assert saved["pendingDecisionId"] is None

    with open(paths["next_action_file"], encoding="utf-8") as handle:
        next_action = json.load(handle)
    assert next_action["terminalState"] == "success"

    with open(paths["summary_file"], encoding="utf-8") as handle:
        summary = handle.read()
    assert "All done" in summary


@pytest.mark.asyncio
async def test_load_events_empty(workspace: str) -> None:
    paths = resolve_artifact_paths(workspace)
    events = await load_events(paths)
    assert events == []


@pytest.mark.asyncio
async def test_load_run_reads_existing_state(workspace: str, ctx: RequestContext) -> None:
    await start_run(
        workspace=workspace,
        scenario="normal",
        goal="test goal",
        request_context=ctx,
        decision_source="internal",
        run_id="run-existing",
    )

    loaded = await load_run(workspace)
    assert loaded is not None
    assert loaded["state"]["runId"] == "run-existing"
    assert loaded["paths"]["browser_profile_dir"].endswith(os.path.join("browser", "run-existing"))


@pytest.mark.asyncio
async def test_invalid_terminal_to_active_transition_raises(workspace: str, ctx: RequestContext) -> None:
    result = await start_run(
        workspace=workspace,
        scenario="normal",
        goal="test",
        request_context=ctx,
        decision_source="internal",
        run_id="run-existing",
    )
    paths = result["paths"]
    state = result["state"]

    await finalize_run(
        paths,
        state,
        status=RunStatus.COMPLETED.value,
        summary="Done",
        observation=None,
        next_action={
            "action": "Stop.",
            "reason": "Done.",
            "terminalState": "success",
        },
    )

    with pytest.raises(ValueError, match="Invalid run status transition"):
        await write_decision_request(
            paths,
            state,
            step_id="S999",
            observation=Observation(url="http://example.test", title="done"),
            summary="Should not reopen a completed run.",
        )
