"""File-based persistence for benchmark run state and events."""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

from .types import RunStatus


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def resolve_artifact_paths(workspace: str) -> dict[str, str]:
    """Compute all artifact file paths for a workspace."""
    root = os.path.join(workspace, ".copilot-agent-kit")
    return {
        "root": root,
        "state_dir": os.path.join(root, "state"),
        "logs_dir": os.path.join(root, "logs"),
        "artifacts_dir": os.path.join(root, "artifacts"),
        "queue_dir": os.path.join(root, "queue"),
        "state_file": os.path.join(root, "state", "run-state.json"),
        "events_file": os.path.join(root, "logs", "agent-events.jsonl"),
        "summary_file": os.path.join(root, "artifacts", "last-summary.md"),
        "next_action_file": os.path.join(root, "queue", "next-action.json"),
        "screenshot_dir": os.path.join(root, "artifacts", "screens"),
    }


def _ensure_dirs(paths: dict[str, str]) -> None:
    for key in ("state_dir", "logs_dir", "artifacts_dir", "queue_dir", "screenshot_dir"):
        os.makedirs(paths[key], exist_ok=True)


def _write_json(file_path: str, value: Any) -> None:
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(value, f, indent=2, ensure_ascii=False)
        f.write("\n")


def _append_jsonl(file_path: str, value: Any) -> None:
    with open(file_path, "a", encoding="utf-8") as f:
        json.dump(value, f, ensure_ascii=False)
        f.write("\n")


def _render_summary(
    state: dict[str, Any],
    next_action: dict[str, Any],
    recent_events: list[dict[str, Any]],
) -> str:
    lines = [
        f"# Copilot Run Summary: {state['runId']}",
        "",
        f"- Scenario: {state['scenario']}",
        f"- Goal: {state['goal']}",
        f"- Status: {state['status']}",
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

    if recent_events:
        lines.append("")
        lines.append("## Recent Events")
        lines.append("")
        for event in recent_events[-5:]:
            lines.append(
                f"- `{event['timestamp']}` `{event['stepId']}` "
                f"`{event['status']}`: {event['summary']}"
            )

    return "\n".join(lines) + "\n"


async def start_run(
    *,
    workspace: str,
    scenario: str,
    goal: str,
    request_context: Any,
) -> dict[str, Any]:
    """Initialize a new benchmark run with state files."""
    paths = resolve_artifact_paths(workspace)
    _ensure_dirs(paths)

    state: dict[str, Any] = {
        "version": 1,
        "runId": f"run-{int(datetime.now(tz=timezone.utc).timestamp() * 1000)}",
        "scenario": scenario,
        "goal": goal,
        "requestContext": asdict(request_context) if hasattr(request_context, "__dataclass_fields__") else request_context,
        "status": RunStatus.ACTIVE.value,
        "createdAt": _now_iso(),
        "updatedAt": _now_iso(),
        "stepsRecorded": 0,
        "lastSummary": None,
    }

    next_action: dict[str, Any] = {
        "runId": state["runId"],
        "updatedAt": state["updatedAt"],
        "action": "Open the request page, observe the current state, and choose one bounded next action.",
        "reason": "No execution steps have been recorded yet.",
    }

    _write_json(paths["state_file"], state)
    _write_json(paths["next_action_file"], next_action)
    with open(paths["summary_file"], "w", encoding="utf-8") as f:
        f.write(_render_summary(state, next_action, []))

    return {"paths": paths, "state": state}


async def record_event(
    paths: dict[str, str],
    *,
    state: dict[str, Any],
    step_id: str,
    status: str,
    summary: str,
    observation: Any,
    decision: Any,
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
    }

    state["updatedAt"] = timestamp
    state["stepsRecorded"] = state.get("stepsRecorded", 0) + 1
    state["lastSummary"] = summary
    _append_jsonl(paths["events_file"], event)
    _write_json(paths["state_file"], state)


async def load_events(paths: dict[str, str]) -> list[dict[str, Any]]:
    """Load all events from the JSONL file."""
    events_file = paths["events_file"]
    if not os.path.exists(events_file):
        return []
    with open(events_file, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


async def finalize_run(
    paths: dict[str, str],
    state: dict[str, Any],
    *,
    status: str,
    summary: str,
    observation: Any,
    next_action: dict[str, Any],
) -> None:
    """Finalize the run: update state, next-action, and summary."""
    state["status"] = status
    state["updatedAt"] = _now_iso()
    state["lastSummary"] = summary

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

    events = await load_events(paths)
    with open(paths["summary_file"], "w", encoding="utf-8") as f:
        f.write(_render_summary(state, next_action, events))
