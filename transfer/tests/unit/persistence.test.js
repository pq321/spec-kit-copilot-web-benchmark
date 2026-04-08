import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, readFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { finalizeRun, loadEvents, recordEvent, resolveArtifactPaths, startRun } from "../../src/benchmark/persistence.js";
import { RUN_STATUS, createRequestContext } from "../../src/benchmark/types.js";

test("startRun creates the continuity files", async () => {
  const workspace = await mkdtemp(path.join(os.tmpdir(), "ghc-web-benchmark-"));
  const { paths, state } = await startRun({
    workspace,
    scenario: "normal",
    goal: "Exercise the benchmark persistence layer",
    requestContext: createRequestContext({ scenario: "normal" })
  });

  const stateFile = JSON.parse(await readFile(paths.stateFile, "utf8"));
  const nextAction = JSON.parse(await readFile(paths.nextActionFile, "utf8"));
  const summary = await readFile(paths.summaryFile, "utf8");

  assert.equal(stateFile.runId, state.runId);
  assert.match(nextAction.action, /Open the request page/);
  assert.match(summary, /No steps recorded yet/);
});

test("recordEvent and finalizeRun update status and summary", async () => {
  const workspace = await mkdtemp(path.join(os.tmpdir(), "ghc-web-benchmark-"));
  const { paths, state } = await startRun({
    workspace,
    scenario: "manual_review",
    goal: "Exercise the benchmark persistence layer",
    requestContext: createRequestContext({ scenario: "manual_review" })
  });

  await recordEvent(paths, {
    state,
    stepId: "S001",
    status: "progress",
    summary: "Selected the target system.",
    observation: {
      url: "http://127.0.0.1/request.html?scenario=manual_review",
      title: "Permission Request Workflow",
      screenshotPath: "screen.png"
    },
    decision: {
      locatorStrategy: "role",
      reason: "The system was not selected yet."
    }
  });

  await finalizeRun(paths, state, {
    status: RUN_STATUS.BLOCKED,
    summary: "A human approval gate was reached.",
    observation: {
      url: "http://127.0.0.1/request.html?scenario=manual_review",
      screenshotPath: "screen.png"
    },
    nextAction: {
      action: "Escalate to the designated human approver.",
      reason: "The workflow reached manual approval.",
      terminalState: "manual_approval_required"
    }
  });

  const events = await loadEvents(paths);
  const stateFile = JSON.parse(await readFile(paths.stateFile, "utf8"));
  const summary = await readFile(paths.summaryFile, "utf8");

  assert.equal(events.length, 1);
  assert.equal(stateFile.status, RUN_STATUS.BLOCKED);
  assert.match(summary, /Escalate to the designated human approver/);
  assert.deepEqual(resolveArtifactPaths(workspace).root, paths.root);
});
