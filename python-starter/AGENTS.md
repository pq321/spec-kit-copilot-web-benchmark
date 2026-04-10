# GHC Agentic Contract

This repository is a GitHub Copilot Chat / Agent mode starter for resilient web
automation in restricted enterprise environments.

## Purpose

Use this file as the cross-tool operating contract for Copilot, Codex, Claude
Code, and any other agent that can read `AGENTS.md`.

## Always-On Rules

- Treat `.github/copilot-instructions.md` as the project-level rule set for
  GitHub Copilot.
- Treat `.copilot-agent-kit/` as runtime evidence, not durable business memory.
- Treat `docs/site-runbooks/<site-slug>.md` as the durable per-site SSOT.
- Prefer Python + conda, Playwright-first execution, and JSON/JSONL continuity
  files.
- Prefer semantic locators before CSS and XPath.
- Never restart from step 1 when state and runbook prove earlier steps are
  already complete.
- On unresolved locator mismatch, flush trace, update the site runbook, record
  the missing human input, and only then escalate.
- Do not copy skill content into chat or into `copilot-instructions`; use
  `.github/skills/*/SKILL.md`.

## Layering Model

- `.github/copilot-instructions.md`
  Project-wide rules that should always apply.
- `.github/instructions/*.instructions.md`
  Path- and language-specific guidance.
- `.github/agents/*.agent.md`
  Role-focused agent personas.
- `.github/prompts/*.prompt.md`
  One-shot workflow entrypoints.
- `.github/skills/*/SKILL.md`
  Multi-step reusable workflows.
- `.vscode/mcp.json`
  Remote MCP server wiring.
- `.github/hooks/policy.json`
  Deterministic guardrails and audit hooks.

## Operating Expectations

- Read run-state, next-action, last-summary, recent events, and the site
  runbook before acting.
- Prefer one bounded action per turn.
- Persist evidence after each meaningful action.
- Update the site runbook whenever a step, locator pattern, or blocker becomes
  reusable knowledge.
- Use custom agents and skills for specialization instead of growing one giant
  instruction file.
