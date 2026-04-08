---
description: Refresh the persisted Markdown summary and next action guidance for Copilot continuity.
---

## User Input

```text
$ARGUMENTS
```

## Outline

1. Read `.copilot-agent-kit/state/run-state.json`.
2. Read the latest entries in `.copilot-agent-kit/logs/agent-events.jsonl`.
3. Regenerate `.copilot-agent-kit/artifacts/last-summary.md`.
4. Regenerate `.copilot-agent-kit/queue/next-action.json`.
5. Report the current run status, latest completed step, and recommended next action.

## Rules

- Keep the Markdown summary concise and action-oriented.
- The next action MUST be a single bounded step, not a broad project goal.
- If the run is blocked, the next action MUST name the approval or dependency that is missing.
