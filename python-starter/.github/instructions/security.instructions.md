---
applyTo: ".github/hooks/**/*,.vscode/mcp.json,.devcontainer/**/*,environment.yml"
---

## Security and Enterprise Guardrails

- Default to no external business API usage.
- Prefer company-approved package sources, mirrors, and browser caches.
- Keep tool permissions minimal; not every agent should have shell or broad MCP access.
- Hooks should enforce guardrails and audit, not embed core business logic.
- Avoid storing credentials, cookies, or sensitive runtime dumps in tracked files.
