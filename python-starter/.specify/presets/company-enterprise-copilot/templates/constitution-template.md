# [PROJECT_NAME] Constitution

## Core Principles

### I. Internal Sources Only
[PRINCIPLE_1_DESCRIPTION]
All dependency installation, template retrieval, and runtime tooling MUST
resolve through approved internal sources such as
`[INTERNAL_CONDA_CHANNEL_URL]` and `[INTERNAL_GIT_MIRROR_URL]`. Public package
registries MAY only be used on approved packaging infrastructure and MUST NOT
be referenced in target-host runbooks.

### II. External API Default Deny
[PRINCIPLE_2_DESCRIPTION]
Generated application code MUST default to zero external business API usage
unless the feature specification explicitly authorizes a named external
dependency and documents the approval owner, data classification impact, and
fallback behavior when that dependency is unavailable.

### III. Modular Boundaries Are Mandatory
[PRINCIPLE_3_DESCRIPTION]
Automation code MUST separate policy, execution, state persistence, logging,
and learned site procedure concerns. Modules that combine multiple
responsibilities MUST be split before expansion.

### IV. Every Step Must Be Resumable
[PRINCIPLE_4_DESCRIPTION]
Any step an agent may execute more than once MUST be idempotent, emit explicit
success / failure / blocked status, and write enough state for a fresh agent
turn to resume without manual terminal transcript reconstruction.

### V. Trace, Runbook, and Resume Memory
[PRINCIPLE_5_DESCRIPTION]
All agent-facing automation MUST emit machine-readable trace, human-readable
summary, and a durable Markdown runbook SSOT so future turns can continue from
the first unfinished step instead of re-learning verified steps.

## Enterprise Constraints

[SECTION_2_CONTENT]
- Approved conda channel: `[INTERNAL_CONDA_CHANNEL_URL]`
- Approved package name for Spec Kit: `[INTERNAL_SPECIFY_PACKAGE]`
- Approved approval owner: `[PACKAGE_APPROVAL_OWNER]`
- Default runtime log root: `.copilot-agent-kit/`
- Default durable runbook root: `docs/site-runbooks/`
- Manual approval gates: `[HUMAN_APPROVAL_GATES]`

## Delivery Workflow

[SECTION_3_CONTENT]
- Planning artifacts MUST reference the persisted state files used for Copilot continuity.
- Plans MUST define how failures are summarized, where next actions are written, and which
  steps require human approval.
- Tasks MUST identify which actions update state, which actions append JSONL logs, which
  actions refresh the Markdown summary, and which actions update the durable runbook SSOT.

## Governance

[GOVERNANCE_RULES]
This constitution is the authoritative source for runtime policy. `.github/agents/` and
`.github/prompts/` files are generated execution surfaces and MUST NOT be treated as the
canonical governance body. `.copilot-agent-kit/` stores runtime evidence, while
`docs/site-runbooks/<site-slug>.md` stores durable learned procedure. Amendments require an
explicit version bump, date update, and a review of any dependent preset, extension, or
runner artifacts that encode policy behavior.

**Version**: [CONSTITUTION_VERSION] | **Ratified**: [RATIFICATION_DATE] | **Last Amended**: [LAST_AMENDED_DATE]
