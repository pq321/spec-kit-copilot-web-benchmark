import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { RUN_STATUS } from "./types.js";

function nowIso() {
  return new Date().toISOString();
}

export function resolveArtifactPaths(workspace) {
  const root = path.join(workspace, ".copilot-agent-kit");
  return {
    root,
    stateDir: path.join(root, "state"),
    logsDir: path.join(root, "logs"),
    artifactsDir: path.join(root, "artifacts"),
    queueDir: path.join(root, "queue"),
    stateFile: path.join(root, "state", "run-state.txton"),
    eventsFile: path.join(root, "logs", "agent-events.txtonl"),
    summaryFile: path.join(root, "artifacts", "last-summary.md"),
    nextActionFile: path.join(root, "queue", "next-action.txton"),
    screenshotDir: path.join(root, "artifacts", "screens")
  };
}

async function ensureDirs(paths) {
  await Promise.all([
    mkdir(paths.stateDir, { recursive: true }),
    mkdir(paths.logsDir, { recursive: true }),
    mkdir(paths.artifactsDir, { recursive: true }),
    mkdir(paths.queueDir, { recursive: true }),
    mkdir(paths.screenshotDir, { recursive: true })
  ]);
}

async function writeJson(filePath, value) {
  await writeFile(filePath, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}

async function appendJsonl(filePath, value) {
  let existing = "";
  try {
    existing = await readFile(filePath, "utf8");
  } catch {
    existing = "";
  }
  await writeFile(filePath, `${existing}${JSON.stringify(value)}\n`, "utf8");
}

function renderSummary(state, nextAction, recentEvents) {
  const lines = [
    `# Copilot Run Summary: ${state.runId}`,
    "",
    `- Scenario: ${state.scenario}`,
    `- Goal: ${state.goal}`,
    `- Status: ${state.status}`,
    `- Steps recorded: ${state.stepsRecorded}`,
    `- Last updated: ${state.updatedAt}`,
    "",
    "## Latest Summary",
    "",
    state.lastSummary || "No steps recorded yet.",
    "",
    "## Next Action",
    "",
    `- Action: ${nextAction.action}`,
    `- Reason: ${nextAction.reason}`
  ];

  if (recentEvents.length > 0) {
    lines.push("", "## Recent Events", "");
    for (const event of recentEvents.slice(-5)) {
      lines.push(`- \`${event.timestamp}\` \`${event.stepId}\` \`${event.status}\`: ${event.summary}`);
    }
  }

  return `${lines.join("\n")}\n`;
}

export async function startRun({ workspace, scenario, goal, requestContext }) {
  const paths = resolveArtifactPaths(workspace);
  await ensureDirs(paths);

  const state = {
    version: 1,
    runId: `run-${Date.now()}`,
    scenario,
    goal,
    requestContext,
    status: RUN_STATUS.ACTIVE,
    createdAt: nowIso(),
    updatedAt: nowIso(),
    stepsRecorded: 0,
    lastSummary: null
  };

  const nextAction = {
    runId: state.runId,
    updatedAt: state.updatedAt,
    action: "Open the request page, observe the current state, and choose one bounded next action.",
    reason: "No execution steps have been recorded yet."
  };

  await writeJson(paths.stateFile, state);
  await writeJson(paths.nextActionFile, nextAction);
  await writeFile(paths.summaryFile, renderSummary(state, nextAction, []), "utf8");
  return { paths, state };
}

export async function recordEvent(paths, { state, stepId, status, summary, observation, decision }) {
  const timestamp = nowIso();
  const event = {
    timestamp,
    stepId,
    status,
    summary,
    pageUrl: observation?.url || null,
    pageTitle: observation?.title || null,
    locatorStrategy: decision?.locatorStrategy || null,
    reason: decision?.reason || null,
    screenshotPath: observation?.screenshotPath || null
  };

  state.updatedAt = timestamp;
  state.stepsRecorded += 1;
  state.lastSummary = summary;
  await appendJsonl(paths.eventsFile, event);
  await writeJson(paths.stateFile, state);
}

export async function loadEvents(paths) {
  try {
    const raw = await readFile(paths.eventsFile, "utf8");
    return raw
      .split(/\r?\n/)
      .filter(Boolean)
      .map((line) => JSON.parse(line));
  } catch {
    return [];
  }
}

export async function finalizeRun(paths, state, { status, summary, observation, nextAction }) {
  state.status = status;
  state.updatedAt = nowIso();
  state.lastSummary = summary;

  await writeJson(paths.stateFile, state);
  await writeJson(paths.nextActionFile, {
    runId: state.runId,
    updatedAt: state.updatedAt,
    action: nextAction.action,
    reason: nextAction.reason,
    terminalState: nextAction.terminalState || null,
    pageUrl: observation?.url || null,
    screenshotPath: observation?.screenshotPath || null
  });

  const events = await loadEvents(paths);
  await writeFile(paths.summaryFile, renderSummary(state, nextAction, events), "utf8");
}
