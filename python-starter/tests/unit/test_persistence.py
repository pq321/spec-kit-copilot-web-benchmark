"""Unit tests for persistence.py — file-based run state and events."""

from __future__ import annotations

import json
import os
import tempfile

import pytest

from benchmark.persistence import (
    finalize_run,
    load_events,
    record_event,
    resolve_artifact_paths,
    start_run,
)
from benchmark.types import RequestContext, RunStatus


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
    )
    paths = result["paths"]
    state = result["state"]

    assert os.path.exists(paths["state_file"])
    assert os.path.exists(paths["next_action_file"])
    assert os.path.exists(paths["summary_file"])

    with open(paths["state_file"]) as f:
        saved = json.load(f)
    assert saved["scenario"] == "normal"
    assert saved["status"] == RunStatus.ACTIVE.value
    assert saved["stepsRecorded"] == 0


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

    with open(paths["state_file"]) as f:
        saved = json.load(f)
    assert saved["status"] == RunStatus.COMPLETED.value
    assert saved["lastSummary"] == "All done"

    with open(paths["next_action_file"]) as f:
        na = json.load(f)
    assert na["terminalState"] == "success"

    with open(paths["summary_file"]) as f:
        summary = f.read()
    assert "All done" in summary


@pytest.mark.asyncio
async def test_load_events_empty(workspace: str) -> None:
    paths = resolve_artifact_paths(workspace)
    events = await load_events(paths)
    assert events == []
