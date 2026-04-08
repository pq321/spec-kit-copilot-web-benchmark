# [PROJECT NAME] Development Guidelines

Auto-generated from all feature plans. Last updated: [DATE]

## Active Technologies

[EXTRACTED FROM ALL PLAN.MD FILES]

## Continuity Files

Always read these before taking the next action:

- `.copilot-agent-kit/state/run-state.json`
- `.copilot-agent-kit/queue/next-action.json`
- `.copilot-agent-kit/artifacts/last-summary.md`
- `.copilot-agent-kit/logs/agent-events.jsonl`
- `docs/site-runbooks/<site-slug>.md` when it exists

If a terminal step has already run, do not ask the user to paste logs when the
persisted state files and runbook already contain the required status, summary,
next action, and verified step history.

## Project Structure

```text
[ACTUAL STRUCTURE FROM PLANS]
```

## Commands

[ONLY COMMANDS FOR ACTIVE TECHNOLOGIES]

## Code Style

[LANGUAGE-SPECIFIC, ONLY FOR LANGUAGES IN USE]

## Recent Changes

[LAST 3 FEATURES AND WHAT THEY ADDED]

<!-- MANUAL ADDITIONS START -->
## Enterprise Runtime Rules

- Prefer company-approved package sources and mirrors.
- Default to no external business API use unless the feature spec explicitly approves it.
- Treat JSONL logs, JSON state, and the site runbook as the continuity source of truth.
- Execute one bounded step at a time, then refresh the continuity files and runbook.
- On unresolved locator mismatch, write trace and runbook updates before asking for help.
<!-- MANUAL ADDITIONS END -->
