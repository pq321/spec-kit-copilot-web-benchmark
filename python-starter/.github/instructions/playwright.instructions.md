---
applyTo: "site/**/*,src/benchmark/**/*"
---

## Playwright Rules

- Prefer `role + accessible name`, then `label`, then stable text, then
  `data-testid`, then CSS, then XPath.
- Observe the page before each action and after each meaningful mutation.
- Do not use raw DOM dumps as the main decision surface when a smaller snapshot
  or accessibility-oriented structure will do.
- Escalate unresolved locator ambiguity only after trace and runbook updates are
  written.
- Any browser-side retry rule must be visible in trace and explain why it is
  safe.
