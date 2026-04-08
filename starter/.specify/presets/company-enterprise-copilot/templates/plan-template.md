# Implementation Plan: [FEATURE_NAME]

## Technical Context

- Language/Version: [LANGUAGE_VERSION]
- Primary Dependencies: [PRIMARY_DEPENDENCIES]
- Storage: [STORAGE]
- Project Type: [PROJECT_TYPE]
- Approved package source: [INTERNAL_CONDA_CHANNEL_URL]
- External API usage: [APPROVED_EXTERNAL_APIS_OR_NONE]

## Constitution Check

- Internal-source-only rule satisfied
- External API default deny satisfied
- Module boundaries defined
- Resumable execution strategy defined
- Dual-format logging strategy defined

## Copilot Continuity Contract

- State file: `.copilot-agent-kit/state/run-state.txton`
- Event log: `.copilot-agent-kit/logs/agent-events.txtonl`
- Markdown summary: `.copilot-agent-kit/artifacts/last-summary.md`
- Next action queue: `.copilot-agent-kit/queue/next-action.txton`
- Required human approval gates: [HUMAN_APPROVAL_GATES]

## Phase 0 Research

- Resolve all `NEEDS CLARIFICATION` markers
- Confirm approved internal packages exist for each dependency
- Confirm no unapproved external API dependency has slipped into the design

## Phase 1 Design

- Define module boundaries for policy, runner, state, logging, and bridge
- Specify which steps update state and which steps refresh the Markdown summary
- Document failure normalization and retry rules

## Phase 2 Delivery Readiness

- Every implementation step must identify its output artifacts
- Every automation step must identify its status transition
- Every destructive or privileged action must identify its human approval owner
