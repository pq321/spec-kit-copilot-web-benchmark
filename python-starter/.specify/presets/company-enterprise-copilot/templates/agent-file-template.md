# [PROJECT NAME] Development Guidelines

Auto-generated from all feature plans. Last updated: [DATE]

## Active Technologies

[EXTRACTED FROM ALL PLAN.MD FILES]

## Continuity Files

Always read these before taking the next action:

- `.copilot-agent-kit/state/run-state.txton`
- `.copilot-agent-kit/queue/next-action.txton`
- `.copilot-agent-kit/artifacts/last-summary.md`

If a terminal step has already run, do not ask the user to paste logs when the persisted
state files already contain the required status, summary, and next action.

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
- Treat JSONL logs and Markdown summaries as the source of truth for task continuity.
- Execute one bounded step at a time, then refresh the continuity files.
<!-- MANUAL ADDITIONS END -->
