---
description: Resume a single bounded Copilot action from persisted state and avoid asking the user to paste logs when continuity files already exist.
---

## User Input

```text
$ARGUMENTS
```

You MUST begin by reading these files if they exist:

- `.copilot-agent-kit/state/run-state.json`
- `.copilot-agent-kit/queue/next-action.json`
- `.copilot-agent-kit/artifacts/last-summary.md`
- `.copilot-agent-kit/logs/agent-events.jsonl`

## Outline

1. Load the persisted run state and determine the current status.
2. Load the recommended next action from `next-action.json`.
3. If the summary already contains the last command outcome, do NOT ask the user to paste logs.
4. Treat the turn as request/response based and execute exactly one bounded next step.
5. After that step completes, refresh the JSONL log, Markdown summary, and next action recommendation.
6. Stop and report what changed plus the next bounded step.

## Rules

- Prefer persisted artifacts over chat history.
- If the run is blocked, ask only for the missing approval or missing dependency.
- If the last step failed, summarize the failure from persisted files before proposing a fix.
