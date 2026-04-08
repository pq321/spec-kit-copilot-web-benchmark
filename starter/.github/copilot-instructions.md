# GHC Web Automation Benchmark Guidance

Auto-generated baseline replaced with repository-specific web automation rules.

## Mission

You are operating inside a benchmark repository that measures whether GitHub
Copilot can behave like a resilient web automation agent.

Success is not "clicked through once." Success is:

- observed page state before acting
- chose stable locators before brittle ones
- handled unlock prerequisites and alternate branches
- persisted enough evidence for the next turn to continue
- stopped and escalated when automation should not continue

## Required Runtime Artifacts

Always read these before taking the next action:

- `.copilot-agent-kit/state/run-state.txton`
- `.copilot-agent-kit/queue/next-action.txton`
- `.copilot-agent-kit/artifacts/last-summary.md`
- `.copilot-agent-kit/logs/agent-events.txtonl`

If those files exist, do not ask the user to paste terminal logs until you have
checked them.

## Locator Policy

When selecting page targets, use this priority order:

1. `role + accessible name`
2. `label`
3. stable visible text
4. `data-testid`
5. CSS fallback
6. XPath only as last resort

Never jump to XPath first when a semantic locator is available.

## Action Policy

Every step must follow this loop:

1. observe current page state
2. classify current state
3. choose one bounded next action
4. execute that action
5. persist evidence and next action

Do not blindly chain clicks without re-observing the page.

## Required Branch Handling

You must explicitly recognize and handle:

- `already_requested`
- `disabled_until_prerequisite`
- `manual_approval_required`
- `permission_not_available`
- `transient_failure`
- `unknown_state`

If a button is disabled, first determine why it is disabled before retrying.

## Escalation Rules

Stop and escalate with evidence if you encounter:

- CAPTCHA or human-verification challenges
- SSO or MFA walls
- true manual approval steps
- ambiguous page state beyond the supported decision rules
- repeated failures without new evidence

Escalation must include:

- current URL
- page title
- key banner or status text
- attempted locator strategy
- screenshot path
- recommended next action

## Repository Structure

```text
.github/
.specify/
.copilot-agent-kit/
site/
src/benchmark/
tests/
```

## Local Commands

```text
npm install
npx playwright install chromium
npm run test
npm run benchmark:normal
npm run benchmark:manual-review
```

## Output Expectations

At the end of every meaningful automation step, refresh:

- `.copilot-agent-kit/state/run-state.txton`
- `.copilot-agent-kit/logs/agent-events.txtonl`
- `.copilot-agent-kit/artifacts/last-summary.md`
- `.copilot-agent-kit/queue/next-action.txton`

Never claim the benchmark passed unless the scenario result and continuity
artifacts are both updated.
