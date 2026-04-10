# GHC Web Automation Benchmark

This repository is a controlled benchmark for a Python starter agentic loop
backing GitHub Copilot Chat/Agent (GHC). It measures whether an agent can make
one safe, well-evidenced browser decision at a time on a fake
permission-request site.

## Operating Modes

- `internal baseline`: local Python + Playwright policy loop; no external APIs
  by default
- `ghc external decision`: request/response turns where GHC reads the current
  state and returns one bounded next action

Both modes share the same continuity contract in `.copilot-agent-kit/`:

- `state/run-state.json`
- `queue/next-action.json`
- `logs/agent-events.jsonl`
- `artifacts/last-summary.md`

## What This Repo Contains

- `.github/copilot-instructions.md` and `copilot-instructions.md`
- `AGENTS.md`
- `.github/instructions/`, `.github/agents/`, `.github/skills/`, and `.github/hooks/`
- `.specify/memory/constitution.md`
- `.specify/extensions/copilot-loop/commands/`
- `.vscode/mcp.json` and `.devcontainer/devcontainer.json`
- `environment.yml`
- `docs/reports/ghc-chat-agentic-retrofit-report.md`
- `site/`
- `src/benchmark/`
- `tests/unit/` and `tests/e2e/`

## Benchmark Scenarios

- `normal`
- `already_requested`
- `prerequisite_unlock`
- `ambiguous_locator`
- `dynamic_dom`
- `manual_review`
- `failure_recovery`

## Local Setup

```powershell
conda env create -f environment.yml
conda activate ghc-web-automation-benchmark
$env:PYTHONPATH="src"
python -m playwright install chromium
pytest
python -m benchmark.cli --scenario normal
```

If your environment uses internal mirrors, replace the placeholders in
`environment.yml` or set:

```powershell
$env:PLAYWRIGHT_DOWNLOAD_HOST="<company-playwright-browser-mirror>"
$env:PLAYWRIGHT_BROWSERS_PATH="<company-playwright-browser-cache>"
```

## Workflow

1. Read `.github/copilot-instructions.md`.
2. Read `.copilot-agent-kit/artifacts/last-summary.md` if it exists.
3. Read `run-state.json`, `next-action.json`, and `agent-events.jsonl` before
   taking a new step.
4. Execute or recommend exactly one bounded action.
5. Refresh the continuity artifacts before ending the turn.

## GHC Chat Retrofit

This starter now includes a layered GitHub Copilot customization stack for
agentic web automation:

- repository instructions
- `AGENTS.md`
- scoped `.instructions.md`
- custom agents
- reusable skills
- MCP server templates
- hook scaffolding
- external runtime trace + site runbooks

See [docs/reports/ghc-chat-agentic-retrofit-report.md](docs/reports/ghc-chat-agentic-retrofit-report.md).

## Key Rule

This benchmark rewards correct stopping behavior, not fake success. If the flow
cannot continue safely, stop, persist evidence, and record the next action
instead of guessing.
