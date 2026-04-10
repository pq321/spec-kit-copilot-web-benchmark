---
applyTo: "**/*.py"
---

## Python Runtime Rules

- Keep policy, execution, persistence, and observation in separate modules.
- Treat run-state and next-action as the runtime state machine contract.
- Prefer explicit enums and typed records for statuses and actions.
- All automation state changes must be reproducible from files, not only chat
  history.
- Avoid hidden globals and implicit retries.
- Any new runtime capability must include unit coverage for state transitions.
