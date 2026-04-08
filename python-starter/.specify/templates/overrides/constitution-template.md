# [PROJECT_NAME] Constitution

## Core Principles

### I. Playwright First
[PRINCIPLE_1_DESCRIPTION]
Browser execution MUST use Playwright as the primary automation layer and all
automation prompts MUST describe deterministic browser actions plus evidence
checks.

### II. Semantic Locator Order
[PRINCIPLE_2_DESCRIPTION]
Locator resolution MUST prioritize role, label, stable text, and `data-testid`
before CSS fallback and XPath.

### III. Observe Then Decide
[PRINCIPLE_3_DESCRIPTION]
Every automation step MUST observe current page state before choosing the next
action.

### IV. Explicit Branch Handling
[PRINCIPLE_4_DESCRIPTION]
Automation MUST recognize alternate states such as already-requested, blocked by
prerequisite, manual review, and transient failure.

### V. Trace, Learning, and Resume Before Completion
[PRINCIPLE_5_DESCRIPTION]
The workflow MUST persist runtime trace, update a durable per-site Markdown
runbook, and resume from the first unfinished step instead of retrying already
verified steps from the beginning.

## Benchmark Constraints

[SECTION_2_CONTENT]
- Controlled or fake target sites only
- Production sites out of scope until escalation rules are defined
- `.copilot-agent-kit/` is the required runtime continuity root
- `docs/site-runbooks/<site-slug>.md` is the required per-site SSOT path
- Locator mismatches MUST be escalated only after trace and runbook updates are written

## Delivery Workflow

[SECTION_3_CONTENT]
- Execute one bounded action at a time
- Refresh run artifacts after each meaningful step
- Update the per-site runbook after each newly verified step or blocker
- Stop safely when human-only gates or unresolved locator mismatches appear

## Governance

[GOVERNANCE_RULES]
This constitution is the source of truth for benchmark behavior and agent
constraints. Runtime traces are evidence. Per-site Markdown runbooks are the
durable procedure SSOT for future turns.

**Version**: [CONSTITUTION_VERSION] | **Ratified**: [RATIFICATION_DATE] | **Last Amended**: [LAST_AMENDED_DATE]
