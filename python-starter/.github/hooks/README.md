# Hook Templates

This directory contains optional hook scaffolding for GitHub Copilot agent
workflows.

## Purpose

Hooks should provide deterministic control, audit, and trace synchronization.
They should not contain core business logic for browser automation.

## Suggested Events

- `SessionStart`
- `PreToolUse`
- `PostToolUse`
- `AgentStop`
- `SubagentStop`
- `SessionEnd`

If hooks are disabled by enterprise policy, move the same logic into your MCP
servers or external runner.
