# Playwright Retry Analysis

Use this skill when a step failed and you need to decide whether a retry is
safe or whether the workflow should branch or escalate.

## Decision Rule

- Retry only when the failure is transient and the previous action is idempotent.
- Branch when the page now exposes a different supported state.
- Escalate when repeated failure adds no new evidence.

## Evidence

- Last successful step
- Current page state
- Retry count
- Why the proposed retry or stop is safe
