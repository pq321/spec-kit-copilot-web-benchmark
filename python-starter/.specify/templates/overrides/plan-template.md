# Implementation Plan: [FEATURE_NAME]

## Technical Context

- Language/Version: [LANGUAGE_VERSION]
- Browser execution: Playwright
- Project Type: web automation benchmark
- Continuity root: `.copilot-agent-kit/`
- Durable site runbook: `docs/site-runbooks/<site-slug>.md`

## Constitution Check

- Playwright-first rule satisfied
- Locator priority rule satisfied
- Observe-then-decide loop satisfied
- Explicit branch handling satisfied
- Trace, learning, and resume persistence satisfied

## Benchmark Design

- Define scenario coverage and expected terminal states
- Define observation schema, decision schema, and artifact outputs
- Define the site runbook sections and update points
- Define escalation rules for human-only blockers

## Delivery Rules

- Every scenario must be rerunnable
- Every run must update run-state, event log, summary, next action, and the site runbook when knowledge changed
- Browser actions must be justified by current observation
- Resume must start from the first unfinished verified step, not from step 1 by default
