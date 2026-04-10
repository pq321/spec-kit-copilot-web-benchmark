# GHC Chat Agentic 改造技术报告

## Executive Summary

This starter should not attempt to imitate Claude Code or Codex by pushing all
logic into one giant `.github/copilot-instructions.md`. GitHub Copilot in VS
Code already supports a layered customization model:

1. repository instructions
2. shared `AGENTS.md`
3. scoped `*.instructions.md`
4. custom agents
5. reusable skills
6. MCP tools, resources, and prompts
7. hooks
8. external persistent state and site runbooks

The correct retrofit strategy is to compose these layers instead of overloading
one file.

## Official Capability Map

### Always-On Instructions

- `.github/copilot-instructions.md` provides repository-level instructions for
  GitHub Copilot.
- `AGENTS.md` can be shared across tools and is read automatically by VS Code.
- `.instructions.md` files support scoped guidance through `applyTo`.

Sources:

- [VS Code custom instructions](https://code.visualstudio.com/docs/copilot/customization/custom-instructions)
- [GitHub repository instructions](https://docs.github.com/en/copilot/how-tos/configure-custom-instructions/add-repository-instructions)

### Role-Specific Agents

- `.github/agents/*.agent.md` supports custom agents for specialized workflows.
- Custom agents can be used from agent mode and prompt files.

Sources:

- [VS Code custom agents](https://code.visualstudio.com/docs/copilot/customization/custom-agents)
- [GitHub custom agents](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/cloud-agent/create-custom-agents)

### Skills

- `.github/skills/*/SKILL.md` is the native mechanism for reusable multi-step
  workflows.
- Skills can include supporting scripts, templates, and other resources.
- Skill content should remain in `SKILL.md`, not be duplicated into repository
  instructions.

Sources:

- [GitHub create skills](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/cloud-agent/create-skills)
- [GitHub about agent skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills)

### MCP

- VS Code supports MCP servers through workspace config and devcontainer
  customizations.
- MCP can expose tools, prompts, resources, and server-side instructions.
- For Dev Pod / Remote-SSH, workspace MCP should run on the remote machine.

Sources:

- [VS Code MCP extension guide](https://code.visualstudio.com/api/extension-guides/ai/mcp)
- [VS Code 1.102 MCP update](https://code.visualstudio.com/updates/v1_102)
- [VS Code 1.99 MCP configuration support](https://code.visualstudio.com/updates/v1_99)

### Hooks

- Hooks are suitable for deterministic guardrails, auditing, and trace
  synchronization.
- They should not replace core business logic.

Sources:

- [GitHub Copilot hooks](https://docs.github.com/en/copilot/concepts/agents/coding-agent/about-hooks)
- [VS Code hooks overview](https://code.visualstudio.com/docs/copilot/customization/hooks)
- [VS Code 1.109 hooks update](https://code.visualstudio.com/updates/v1_109)

## Recommended Layered Architecture

### Layer 1: Repository Rules

Use `.github/copilot-instructions.md` for:

- Python + conda first
- Playwright-first automation
- JSON and JSONL continuity contract
- site runbook SSOT
- escalation conditions
- external API default deny

### Layer 2: Cross-Tool Contract

Use `AGENTS.md` for:

- shared operating model across Copilot, Codex, and Claude Code
- separation between runtime evidence and durable site knowledge
- explicit layering model for instructions, skills, MCP, and hooks

### Layer 3: Scoped Instructions

Use `.github/instructions/*.instructions.md` for:

- Python runtime rules
- Playwright and locator rules
- runbook writing rules
- security and guardrail rules

### Layer 4: Custom Agents

Use `.github/agents/*.agent.md` for:

- orchestration
- planning
- page exploration
- implementation
- trace audit
- review

Only the orchestrator should have broad delegation authority.

### Layer 5: Skills

Use `.github/skills/*/SKILL.md` for:

- one-step web automation progression
- trace flushing
- site runbook updates
- locator escalation
- MCP debugging
- retry analysis

### Layer 6: MCP

Use `.vscode/mcp.json` and optionally `.devcontainer/devcontainer.json` to
register remote MCP servers for:

- Playwright browser control
- state access
- trace access
- enterprise-approved shell or ops commands

### Layer 7: Hooks

Use hooks for:

- session-start context hydration
- pre-tool guardrails
- post-tool trace flush
- session-end audit

### Layer 8: External Persistent Harness

Keep:

- `.copilot-agent-kit/`
- `docs/site-runbooks/<site-slug>.md`

These are still required because native Copilot customization does not replace
cross-turn durable state.

## Do Not Do

- Do not copy skill contents into `copilot-instructions.md`.
- Do not let GHC consume huge raw DOM blobs as the default perception surface.
- Do not store critical trace only in the chat transcript.
- Do not keep site-specific knowledge only in transient runtime state.
- Do not grant every agent shell plus all MCP tools.

## Dev Pod / Remote SSH Recommendation

Use a split-plane model:

- Local VS Code: Copilot UI, account, chat, prompt entry
- Remote Dev Pod Linux: Chromium, Playwright, MCP servers, shell, code

This keeps browser execution and MCP tool invocation close to the remote
workspace while preserving local IDE UX.

## Verification Checklist

1. References / Diagnostics confirm repository instructions and `AGENTS.md`
   are loaded.
2. Agent mode can see the custom agents.
3. Skills are discoverable and relevant tasks trigger the right ones.
4. MCP tools and resources are visible from the remote workspace.
5. Hooks append audit events and enforce tool guardrails.
6. The fake site benchmark completes a full request/response loop.
7. Locator mismatch causes trace flush + runbook update before human escalation.

## Community References

Use community examples only as inspiration, not as the normative source:

- [github/awesome-copilot](https://github.com/github/awesome-copilot)
- [Copilot Orchestra](https://github.com/ShepAlderson/copilot-orchestra)
