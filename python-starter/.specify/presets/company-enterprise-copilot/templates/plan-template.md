# Implementation Plan: [FEATURE_NAME]

## Technical Context

- Language/Version: [LANGUAGE_VERSION]
- Primary Dependencies: [PRIMARY_DEPENDENCIES]
- Storage: [STORAGE]
- Project Type: [PROJECT_TYPE]
- Approved package source: [INTERNAL_CONDA_CHANNEL_URL]
- External API usage: [APPROVED_EXTERNAL_APIS_OR_NONE]
- Runtime continuity root: `.copilot-agent-kit/`
- Durable site runbook root: `docs/site-runbooks/`

## Constitution Check

- Internal-source-only rule satisfied
- External API default deny satisfied
- Module boundaries defined
- Resumable execution strategy defined
- Trace + runbook logging strategy defined

## Copilot Continuity Contract

- State file: `.copilot-agent-kit/state/run-state.json`
- Event log: `.copilot-agent-kit/logs/agent-events.jsonl`
- Markdown summary: `.copilot-agent-kit/artifacts/last-summary.md`
- Next action queue: `.copilot-agent-kit/queue/next-action.json`
- Durable runbook: `docs/site-runbooks/<site-slug>.md`
- Required human approval gates: [HUMAN_APPROVAL_GATES]

## Phase 0 Research

- Resolve all `NEEDS CLARIFICATION` markers
- Confirm approved internal packages exist for each dependency
- Confirm no unapproved external API dependency has slipped into the design
- Confirm the target site slug and runbook location

## Phase 1 Design

- Define module boundaries for policy, runner, state, logging, and bridge
- Specify which steps update state, which steps refresh the Markdown summary,
  and which steps update the durable runbook
- Document failure normalization, escalation rules, and resume rules

## Phase 2 Delivery Readiness

- Every implementation step must identify its output artifacts
- Every automation step must identify its status transition
- Every destructive or privileged action must identify its human approval owner
- Every unresolved locator mismatch must identify the trace fields and runbook
  updates required before asking for help
