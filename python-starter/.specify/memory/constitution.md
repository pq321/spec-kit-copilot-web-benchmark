<!--
Sync Impact Report
Version change: 1.0.1 -> 1.1.0
Modified principles:
- V. Evidence Before Completion -> V. Trace, Learning, and Resume Before Completion
Added sections:
- Per-site SSOT runbook clarification in amendment and constraints
Removed sections:
- None
Templates requiring updates:
- updated: .specify/templates/overrides/constitution-template.md
- updated: .specify/presets/company-enterprise-copilot/templates/constitution-template.md
- updated: .github/copilot-instructions.md
- updated: copilot-instructions.md
Follow-up TODOs:
- None
-->
# GHC Web Automation Benchmark Constitution

## Clarifying Amendment to v1.1.0

This amendment expands v1.0.1 without replacing its core approach.

- The benchmark supports two sanctioned modes:
  - `internal baseline`: local Python + Playwright execution with deterministic
    internal policy decisions
  - `ghc external decision`: request/response turns where GHC receives the
    current request context and returns one bounded next action
- Both modes MUST use the same runtime continuity contract:
  - `.copilot-agent-kit/state/run-state.json`
  - `.copilot-agent-kit/queue/next-action.json`
  - `.copilot-agent-kit/logs/agent-events.jsonl`
  - `.copilot-agent-kit/artifacts/last-summary.md`
- Every target site MUST also maintain one durable Markdown SSOT runbook at
  `docs/site-runbooks/<site-slug>.md`. This runbook stores the learned
  procedure, stable locator hints, verified step order, known blockers, and the
  current resume point for that site.
- Runtime trace is execution evidence. The site runbook is long-lived site
  knowledge. Both MUST be updated before the agent asks a human to intervene.
- Repository setup and operator guidance MUST be Python + conda first. Node,
  `npm`, and `npx` instructions are not canonical in this repository.
- External APIs are off by default. They require explicit benchmark support or
  explicit user instruction.
- Organization-specific distribution points such as `<company-conda-channel>`,
  `<company-playwright-browser-mirror>`, and
  `<company-playwright-browser-cache>` are deployment placeholders, not public
  defaults.

## Core Principles

### I. Playwright First

Browser execution MUST use Python Playwright as the primary automation layer.
Natural language prompts may guide decisions, but browser interaction must be
grounded in deterministic Playwright actions and verifiable page observations.

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

### V. Trace, Learning, and Resume Before Completion

Automation is only considered correct when it persists enough evidence for a
fresh turn to continue without repeated trial-and-error. Every meaningful turn
MUST write:

- the observed URL and page title
- banner or status evidence
- chosen locator strategy and attempted locator candidates
- action result and step status
- screenshot or DOM evidence reference
- structured next action
- updates to the per-site runbook for any newly verified step, locator rule,
  prerequisite rule, or blocker

If natural-language task logic cannot be matched to a confident locator after
re-observation and the semantic locator order is exhausted, the agent MUST stop,
flush the runtime trace, update the site runbook with completed steps and the
unresolved ambiguity, and only then ask a human for help.

Future runs MUST read the current runtime artifacts and the site runbook before
acting. Already verified steps MUST NOT be retried from step 1 unless the page
structure changed, the session expired, or the runbook explicitly marks those
steps invalidated.

## Benchmark Constraints

- This repository targets fake or controlled permission-request sites only.
- Production systems, real SSO, MFA, CAPTCHA, and irreversible access changes
  are out of scope for the benchmark.
- External APIs are out of scope unless a benchmark mode explicitly enables
  them.
- The benchmark must reward safe escalation, not blind persistence.
- Browser automation code, policy code, observation code, and persistence code
  must remain in separate modules.
- Per-site durable knowledge MUST live at `docs/site-runbooks/<site-slug>.md`.

## Delivery Workflow

- Build or refine one bounded behavior at a time.
- After every significant automation step, refresh `.copilot-agent-kit/`.
- Before asking for human validation, rerun the relevant scenario and confirm
  the expected terminal state.
- If automation reaches a human-only gate or an unresolved locator mismatch,
  write a structured escalation packet and update the site runbook before
  stopping.
- Promote repeated site-specific facts such as field order, unlock rules,
  stable locators, and approval gates into the site runbook as soon as they are
  verified.
- Resume from the first unfinished step recorded in state and runbook rather
  than replaying already verified steps from the beginning.

## Governance

This constitution governs all benchmark scenarios and benchmark tooling in this
repository. Generated `.github/agents/` and `.github/prompts/` files are
execution surfaces, not the canonical policy source. `.copilot-agent-kit/`
stores runtime evidence, while `docs/site-runbooks/<site-slug>.md` is the
canonical per-site procedure and learning document. Amendments require an
explicit version bump, date update, and a review of dependent templates or
instructions that encode agent behavior.

**Version**: 1.1.0 | **Ratified**: 2026-04-08 | **Last Amended**: 2026-04-09
