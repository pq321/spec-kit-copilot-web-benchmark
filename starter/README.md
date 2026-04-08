# GHC Web Automation Benchmark

This repository is a controlled benchmark for GitHub Copilot Chat/Agent (GHC).

Its purpose is not to automate a real production site. Its purpose is to
measure whether GHC can behave like a resilient web automation agent under
engineering constraints:

- observe the current page before acting
- choose high-semantic locators before brittle selectors
- handle disabled buttons and prerequisite unlocks
- recognize already-requested and manual-review states
- write enough evidence for the next turn to continue without pasted logs

## What This Repo Contains

- `.github/agents/` and `.github/prompts/`
  - Spec Kit Copilot command surfaces
- `.github/copilot-instructions.md`
  - Repository-level rules for GHC
- `.specify/memory/constitution.md`
  - Root governance for the benchmark
- `.copilot-agent-kit/`
  - Runtime continuity artifacts written by the benchmark runner
- `site/`
  - A fake permission-request website with six benchmark scenarios
- `src/benchmark/`
  - Browser adapter, observation layer, policy layer, persistence layer, and runner
- `tests/unit/`
  - Unit tests for policy and persistence behavior
- `tests/e2e/`
  - Playwright benchmark tests across all scenarios

## Benchmark Scenarios

- `normal`
- `already_requested`
- `prerequisite_unlock`
- `ambiguous_locator`
- `dynamic_dom`
- `manual_review`
- `failure_recovery`

## Recommended GHC Workflow

1. Open the repo in VS Code.
2. Read `.github/copilot-instructions.md`.
3. Read `.copilot-agent-kit/artifacts/last-summary.md` if it exists.
4. Use the repo commands and benchmark runner to execute one bounded step at a time.
5. After each step, refresh `.copilot-agent-kit/` artifacts before asking for help.

## Local Commands

```powershell
npm install
npx playwright install chromium
npm run test
npm run benchmark:normal
```

## Key Rule

This repo is designed to reward correct failure handling, not fake success.
If automation cannot continue safely, the correct behavior is to stop, write
evidence, and escalate with a structured next action.
