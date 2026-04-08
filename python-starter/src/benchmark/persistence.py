"""File-based persistence for benchmark run state, requests, and events."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from typing import Any

from .types import (
    RUN_STATE_TRANSITIONS,
    DecisionRequest,
    Observation,
    RequestContext,
    RunStatus,
)


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _safe_unlink(path: str) -> None:
    if os.path.exists(path):
        os.remove(path)


def _safe_rmtree(path: str) -> None:
    if not os.path.isdir(path):
        return
    for entry in os.listdir(path):
        full_path = os.path.join(path, entry)
        if os.path.isdir(full_path):
            _safe_rmtree(full_path)
            os.rmdir(full_path)
        else:
            os.remove(full_path)


def resolve_artifact_paths(workspace: str) -> dict[str, str]:
    """Compute the stable artifact locations for a workspace."""
    root = os.path.join(workspace, ".copilot-agent-kit")
    return {
        "root": root,
        "state_dir": os.path.join(root, "state"),
        "logs_dir": os.path.join(root, "logs"),
        "artifacts_dir": os.path.join(root, "artifacts"),
        "queue_dir": os.path.join(root, "queue"),
        "browser_dir": os.path.join(root, "browser"),
        "state_file": os.path.join(root, "state", "run-state.json"),
        "events_file": os.path.join(root, "logs", "agent-events.jsonl"),
        "summary_file": os.path.join(root, "artifacts", "last-summary.md"),
        "next_action_file": os.path.join(root, "queue", "next-action.json"),
        "decision_request_file": os.path.join(root, "queue", "decision-request.json"),
        "decision_response_file": os.path.join(root, "queue", "decision-response.json"),
        "screenshot_dir": os.path.join(root, "artifacts", "screens"),
    }


def _with_run_paths(paths: dict[str, str], run_id: str) -> dict[str, str]:
    run_paths = dict(paths)
    run_paths["browser_profile_dir"] = os.path.join(paths["browser_dir"], run_id)
    return run_paths


def _ensure_dirs(paths: dict[str, str]) -> None:
    for key in (
        "state_dir",
        "logs_dir",
        "artifacts_dir",
        "queue_dir",
        "browser_dir",
        "screenshot_dir",
    ):
        os.makedirs(paths[key], exist_ok=True)
    if "browser_profile_dir" in paths:
        os.makedirs(paths["browser_profile_dir"], exist_ok=True)


def _to_json_value(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    return value


def _write_json(file_path: str, value: Any) -> None:
    with open(file_path, "w", encoding="utf-8") as handle:
        json.dump(_to_json_value(value), handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def _append_jsonl(file_path: str, value: Any) -> None:
    with open(file_path, "a", encoding="utf-8") as handle:
        json.dump(_to_json_value(value), handle, ensure_ascii=False)
        handle.write("\n")


def _read_json(file_path: str) -> dict[str, Any]:
    with open(file_path, encoding="utf-8") as handle:
        return json.load(handle)


def _write_summary(
    paths: dict[str, str],
    state: dict[str, Any],
    next_action: dict[str, Any],
    recent_events: list[dict[str, Any]],
) -> None:
    lines = [
        f"# Copilot Run Summary: {state['runId']}",
        "",
        f"- Scenario: {state['scenario']}",
        f"- Goal: {state['goal']}",
        f"- Decision source: {state['decisionSource']}",
        f"- Status: {state['status']}",
        f"- Current step: {state['currentStep']}",
        f"- Steps recorded: {state['stepsRecorded']}",
        f"- Last updated: {state['updatedAt']}",
        "",
        "## Latest Summary",
        "",
        state.get("lastSummary") or "No steps recorded yet.",
        "",
        "## Next Action",
        "",
        f"- Action: {next_action['action']}",
        f"- Reason: {next_action['reason']}",
    ]

    if next_action.get("decisionRequestFile"):
        lines.append(f"- Decision request: {next_action['decisionRequestFile']}")

    if recent_events:
        lines.extend(["", "## Recent Events", ""])
        for event in recent_events[-5:]:
            lines.append(
                f"- `{event['timestamp']}` `{event['stepId']}` "
                f"`{event['status']}`: {event['summary']}"
            )

    with open(paths["summary_file"], "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def _set_state_fields(
    state: dict[str, Any],
    *,
    status: str | None = None,
    pending_decision_id: str | None = None,
    terminal_state: str | None = None,
    last_summary: str | None = None,
    last_page_url: str | None = None,
) -> None:
    if status is not None:
        current_status = RunStatus(state["status"])
        next_status = RunStatus(status)
        allowed = RUN_STATE_TRANSITIONS[current_status]
        if next_status not in allowed:
            raise ValueError(
                f"Invalid run status transition: {current_status.value} -> {next_status.value}"
            )
        state["status"] = next_status.value
    state["pendingDecisionId"] = pending_decision_id
    state["terminalState"] = terminal_state
    if last_summary is not None:
        state["lastSummary"] = last_summary
    if last_page_url is not None:
        state["lastPageUrl"] = last_page_url
    state["updatedAt"] = _now_iso()


async def load_events(paths: dict[str, str]) -> list[dict[str, Any]]:
    """Load the JSONL event log for a workspace."""
    events_file = paths["events_file"]
    if not os.path.exists(events_file):
        return []
    with open(events_file, encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


async def start_run(
    *,
    workspace: str,
    scenario: str,
    goal: str,
    request_context: Any,
    decision_source: str = "internal",
    run_id: str | None = None,
) -> dict[str, Any]:
    """Initialize a new benchmark run and clear stale artifacts."""
    base_paths = resolve_artifact_paths(workspace)
    run_id = run_id or f"run-{int(datetime.now(tz=timezone.utc).timestamp() * 1000)}"
    paths = _with_run_paths(base_paths, run_id)
    _ensure_dirs(paths)
    _safe_rmtree(paths["screenshot_dir"])
    os.makedirs(paths["screenshot_dir"], exist_ok=True)
    for file_path in (
        paths["state_file"],
        paths["events_file"],
        paths["summary_file"],
        paths["next_action_file"],
        paths["decision_request_file"],
        paths["decision_response_file"],
    ):
        _safe_unlink(file_path)

    state: dict[str, Any] = {
        "version": 2,
        "runId": run_id,
        "scenario": scenario,
        "goal": goal,
        "requestContext": _to_json_value(request_context),
        "decisionSource": decision_source,
        "status": RunStatus.ACTIVE.value,
        "createdAt": _now_iso(),
        "updatedAt": _now_iso(),
        "currentStep": 0,
        "stepsRecorded": 0,
        "browserProfileDir": paths["browser_profile_dir"],
        "lastPageUrl": None,
        "pendingDecisionId": None,
        "terminalState": None,
        "lastSummary": None,
    }

    next_action: dict[str, Any] = {
        "runId": run_id,
        "updatedAt": state["updatedAt"],
        "action": "Open the request page, observe the current state, and choose one bounded next action.",
        "reason": "No execution steps have been recorded yet.",
    }

    _write_json(paths["state_file"], state)
    _write_json(paths["next_action_file"], next_action)
    _write_summary(paths, state, next_action, [])
    return {"paths": paths, "state": state}


async def load_run(workspace: str) -> dict[str, Any] | None:
    """Load the active run state for a workspace if one exists."""
    paths = resolve_artifact_paths(workspace)
    if not os.path.exists(paths["state_file"]):
        return None
    state = _read_json(paths["state_file"])
    run_paths = _with_run_paths(paths, state["runId"])
    if not state.get("browserProfileDir"):
        state["browserProfileDir"] = run_paths["browser_profile_dir"]
    return {"paths": run_paths, "state": state}


async def write_decision_request(
    paths: dict[str, str],
    state: dict[str, Any],
    *,
    step_id: str,
    observation: Observation,
    summary: str,
) -> dict[str, Any]:
    """Persist the next external-decision request and mark the run as waiting."""
    request = DecisionRequest(
        run_id=state["runId"],
        step_id=step_id,
        scenario=state["scenario"],
        requested_at=_now_iso(),
        summary=summary,
        observation=observation,
        request_context=RequestContext(**state["requestContext"]),
    )
    _write_json(paths["decision_request_file"], {
        "runId": request.run_id,
        "stepId": request.step_id,
        "scenario": request.scenario,
        "requestedAt": request.requested_at,
        "summary": request.summary,
        "observation": asdict(request.observation),
        "requestContext": asdict(request.request_context),
        "allowedActionTypes": request.allowed_action_types,
    })

    _set_state_fields(
        state,
        status=RunStatus.AWAITING_DECISION.value,
        pending_decision_id=step_id,
        last_summary=summary,
        last_page_url=observation.url,
    )
    _write_json(paths["state_file"], state)

    next_action = {
        "runId": state["runId"],
        "updatedAt": state["updatedAt"],
        "action": "Read decision-request.json, write decision-response.json, then rerun step mode with --resume.",
        "reason": summary,
        "decisionRequestFile": paths["decision_request_file"],
        "pageUrl": observation.url,
        "screenshotPath": observation.screenshot_path,
    }
    _write_json(paths["next_action_file"], next_action)
    _write_summary(paths, state, next_action, await load_events(paths))
    return next_action


async def consume_decision_response(
    paths: dict[str, str],
    state: dict[str, Any],
) -> dict[str, Any] | None:
    """Read and remove the pending external-decision response if it exists."""
    file_path = paths["decision_response_file"]
    if not os.path.exists(file_path):
        return None
    payload = _read_json(file_path)
    _safe_unlink(file_path)
    return payload


async def record_event(
    paths: dict[str, str],
    *,
    state: dict[str, Any],
    step_id: str,
    status: str,
    summary: str,
    observation: Any,
    decision: Any,
    count_step: bool = True,
) -> None:
    """Append an event to the JSONL log and update run state."""
    timestamp = _now_iso()
    event: dict[str, Any] = {
        "timestamp": timestamp,
        "stepId": step_id,
        "status": status,
        "summary": summary,
        "pageUrl": getattr(observation, "url", None) if observation else None,
        "pageTitle": getattr(observation, "title", None) if observation else None,
        "locatorStrategy": getattr(decision, "locator_strategy", None) if decision else None,
        "reason": getattr(decision, "reason", None) if decision else None,
        "screenshotPath": getattr(observation, "screenshot_path", None) if observation else None,
        "decision": _to_json_value(decision) if decision else None,
    }

    state["updatedAt"] = timestamp
    if count_step:
        state["currentStep"] = state.get("currentStep", 0) + 1
        state["stepsRecorded"] = state.get("stepsRecorded", 0) + 1
        state["pendingDecisionId"] = None
    state["lastSummary"] = summary
    if observation is not None:
        state["lastPageUrl"] = getattr(observation, "url", None)

    _append_jsonl(paths["events_file"], event)
    _write_json(paths["state_file"], state)


async def finalize_run(
    paths: dict[str, str],
    state: dict[str, Any],
    *,
    status: str,
    summary: str,
    observation: Any,
    next_action: dict[str, Any],
) -> None:
    """Finalize the run state and write terminal next-action/summary files."""
    _set_state_fields(
        state,
        status=status,
        pending_decision_id=None,
        terminal_state=next_action.get("terminalState"),
        last_summary=summary,
        last_page_url=getattr(observation, "url", None) if observation else None,
    )
    _write_json(paths["state_file"], state)
    _write_json(paths["next_action_file"], {
        "runId": state["runId"],
        "updatedAt": state["updatedAt"],
        "action": next_action["action"],
        "reason": next_action["reason"],
        "terminalState": next_action.get("terminalState"),
        "pageUrl": getattr(observation, "url", None) if observation else None,
        "screenshotPath": getattr(observation, "screenshot_path", None) if observation else None,
    })
    _safe_unlink(paths["decision_request_file"])
    _safe_unlink(paths["decision_response_file"])
    _write_summary(paths, state, _read_json(paths["next_action_file"]), await load_events(paths))
