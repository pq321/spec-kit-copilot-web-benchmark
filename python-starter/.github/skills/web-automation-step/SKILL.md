# Web Automation Step

Use this skill when the agent must advance exactly one browser step and preserve
enough evidence for a later turn.

## Workflow

1. Read `run-state.json`, `next-action.json`, `last-summary.md`, and the site
   runbook.
2. Inspect the current observation or request context.
3. Choose one bounded next action.
4. Execute or recommend that action.
5. Flush trace and update the runbook if new knowledge was verified.

## Never

- Do not take multiple unrelated browser actions in one turn.
- Do not ask for pasted logs before checking persisted artifacts.
- Do not restart from step 1 when the runbook already proves earlier progress.
