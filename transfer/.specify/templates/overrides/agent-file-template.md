# [PROJECT NAME] Web Automation Guidance

Auto-generated from all feature plans. Last updated: [DATE]

## Active Technologies

[EXTRACTED FROM ALL PLAN.MD FILES]

## Required Runtime Artifacts

- `.copilot-agent-kit/state/run-state.txton`
- `.copilot-agent-kit/logs/agent-events.txtonl`
- `.copilot-agent-kit/artifacts/last-summary.md`
- `.copilot-agent-kit/queue/next-action.txton`

## Locator Priority

1. role + accessible name
2. label
3. stable visible text
4. data-testid
5. CSS fallback
6. XPath last

## Project Structure

```text
[ACTUAL STRUCTURE FROM PLANS]
```

## Commands

[ONLY COMMANDS FOR ACTIVE TECHNOLOGIES]

## Code Style

[LANGUAGE-SPECIFIC, ONLY FOR LANGUAGES IN USE]

## Recent Changes

[LAST 3 FEATURES AND WHAT THEY ADDED]

<!-- MANUAL ADDITIONS START -->
- Always observe the page before taking the next action.
- Always stop and escalate on human-only gates.
- Never ask for pasted logs before checking `.copilot-agent-kit/`.
<!-- MANUAL ADDITIONS END -->
