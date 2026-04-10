# GHC Web Automation Benchmark Guidance

Repository-specific rules for the Python starter agentic loop.

## Mission

Act like a resilient web automation agent that makes one safe, evidence-backed
decision at a time. Success requires:

- observing page state before acting
- preferring semantic locators over brittle selectors
- handling prerequisite, already-requested, and manual-review branches
- persisting enough evidence for the next turn to continue
- updating the per-site SSOT runbook as the workflow is learned
- stopping instead of guessing when the flow is not safe

## Runtime Contract

Always read these artifacts first when they exist:

- `.copilot-agent-kit/state/run-state.json`
- `.copilot-agent-kit/queue/next-action.json`
- `.copilot-agent-kit/artifacts/last-summary.md`
- `.copilot-agent-kit/logs/agent-events.jsonl`

Also read the per-site runbook if it exists:

- `docs/site-runbooks/<site-slug>.md`

Do not ask for pasted logs before checking the persisted artifacts and runbook.

## Native Customization Stack

Use the repository assets by layer instead of pushing all logic into this file:

- `AGENTS.md` for cross-tool shared rules
- `.github/instructions/*.instructions.md` for scoped guidance
- `.github/agents/*.agent.md` for role-focused personas
- `.github/skills/*/SKILL.md` for reusable workflows
- `.vscode/mcp.json` for remote MCP tools and resources
- `.github/hooks/` for deterministic guardrails and audit

Prefer skills and agents over copying long workflow text into chat.

## Modes

- `internal baseline`: local Python + Playwright execution with internal policy
  decisions and no external APIs by default
- `ghc external decision`: request/response turns where GHC reads the current
  request context and returns exactly one bounded next action

Do not assume a background daemon or long-running autonomous loop in GHC mode.

## Action Policy

Every turn must:

1. observe the current page
2. classify the current state
3. choose one bounded next action
4. execute or recommend that action
5. persist evidence and the next action
6. update the site runbook if the turn verified a reusable step or revealed a durable blocker

## Locator Policy

Use this locator order:

1. `role + accessible name`
2. `label`
3. stable visible text
4. `data-testid`
5. CSS fallback
6. XPath only as the final fallback

## Required Branch Handling

Explicitly handle:

- `already_requested`
- `disabled_until_prerequisite`
- `manual_approval_required`
- `permission_not_available`
- `transient_failure`
- `unknown_state`

If a control is disabled, determine why before retrying.

## Escalation

Stop and escalate with evidence for CAPTCHA, MFA, true manual approval,
unsupported ambiguity, or repeated failures without new evidence.

Unresolved locator mismatch is also an escalation condition. If the current
natural-language step cannot be matched to a confident locator after
re-observation and semantic locator fallback, the agent MUST:

1. write the latest runtime trace
2. update the site runbook with completed steps, attempted locators, and the unresolved step
3. record the exact human input needed
4. only then ask for help

Never restart from step 1 when prior verified steps already exist in state and
runbook, unless the page structure changed or the session is invalid.

## Local Setup

```powershell
conda env create -f environment.yml
conda activate ghc-web-automation-benchmark
$env:PYTHONPATH="src"
python -m playwright install chromium
pytest
python -m benchmark.cli --scenario normal
```

Use organization placeholders such as `<company-conda-channel>`,
`<company-playwright-browser-mirror>`, and
`<company-playwright-browser-cache>` only when your environment requires them.

## Output Expectations

Refresh these after each meaningful step:

- `.copilot-agent-kit/state/run-state.json`
- `.copilot-agent-kit/logs/agent-events.jsonl`
- `.copilot-agent-kit/artifacts/last-summary.md`
- `.copilot-agent-kit/queue/next-action.json`
- `docs/site-runbooks/<site-slug>.md` when knowledge changed

Never claim success unless the scenario result, continuity artifacts, and
durable site runbook are all up to date.
