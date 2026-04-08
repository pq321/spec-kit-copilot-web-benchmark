# Site Runbooks

Each target website MUST maintain one Markdown runbook at:

`docs/site-runbooks/<site-slug>.md`

This file is the durable per-site SSOT. It is not a raw transcript. It is the
normalized procedure and learning document that future agent turns must read
before acting.

## Required Sections

1. `Overview`
   State the target site, workflow goal, and scope boundaries.
2. `Preconditions`
   List login/session assumptions, required roles, and known approval gates.
3. `Verified Steps`
   Record each step that has been successfully executed in a stable way.
4. `Stable Locator Hints`
   Record semantic locators, fallback selectors, and ambiguity notes.
5. `Known Branches`
   Record `already_requested`, prerequisite unlocks, manual approval, and other
   verified branches.
6. `Current Resume Point`
   State the first unfinished step and what evidence proves earlier steps are complete.
7. `Open Questions / Human Input Needed`
   Record unresolved locator mismatches or business ambiguities that require help.

## Update Rules

- Update the runbook after every newly verified step.
- Update it before any escalation to a human.
- Do not restart from step 1 if the runbook already proves earlier steps are complete.
- Invalidate prior steps only when the page structure, policy, or session model changed.
