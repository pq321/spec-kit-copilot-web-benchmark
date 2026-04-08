# GHC Web Automation Benchmark Constitution

## Core Principles

### I. Playwright First

Browser execution MUST use Playwright as the primary automation layer. Natural
language prompts may guide decisions, but browser interaction must be grounded
in deterministic Playwright actions and verifiable page observations.

### II. Semantic Locators Before Brittle Selectors

Locator resolution MUST follow this priority order:

1. `role + accessible name`
2. `label`
3. stable visible text
4. `data-testid`
5. CSS fallback
6. XPath as the final fallback only

XPath MUST NOT be the default strategy.

### III. Observe, Then Decide

Every automation step MUST be structured as:

1. observe current page state
2. classify the state
3. choose one bounded action
4. execute the action
5. persist evidence and next action

Linear "click-next-click-next" flows without observation checkpoints are not
allowed.

### IV. Explicit Branch Handling

The automation policy MUST explicitly detect and handle:

- `already_requested`
- `disabled_until_prerequisite`
- `manual_approval_required`
- `permission_not_available`
- `transient_failure`
- `unknown_state`

If the flow cannot proceed, the benchmark must record why and stop safely.

### V. Evidence Before Completion

Automation is only considered complete when the run persists:

- the observed URL and page title
- banner or status evidence
- chosen locator strategy
- action result
- screenshot or DOM evidence reference
- structured next action

The benchmark MUST be resumable from `.copilot-agent-kit/` without requiring a
human to paste raw logs.

## Benchmark Constraints

- This repository targets fake or controlled permission-request sites only.
- Production systems, real SSO, MFA, CAPTCHA, and irreversible access changes
  are out of scope for the benchmark.
- The benchmark must reward safe escalation, not blind persistence.
- Browser automation code, policy code, observation code, and persistence code
  must remain in separate modules.

## Delivery Workflow

- Build or refine one bounded behavior at a time.
- After every significant automation step, refresh `.copilot-agent-kit/`.
- Before asking for human validation, rerun the relevant scenario and confirm
  the expected terminal state.
- If automation reaches a human-only gate, write a structured escalation packet
  instead of continuing.

## Governance

This constitution governs all benchmark scenarios and benchmark tooling in this
repository. Generated `.github/agents/` and `.github/prompts/` files are
execution surfaces, not the canonical policy source.

**Version**: 1.0.0 | **Ratified**: 2026-04-08 | **Last Amended**: 2026-04-08
