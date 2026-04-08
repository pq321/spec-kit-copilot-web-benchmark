import { chromium } from "@playwright/test";
import { createBrowserAdapter } from "./browser-adapter.js";
import { captureObservation } from "./observation.js";
import { decideNextAction } from "./policy.js";
import { finalizeRun, recordEvent, startRun } from "./persistence.js";
import { ACTION_TYPE, RUN_STATUS, TERMINAL_STATE } from "./types.js";

async function executeDecision(adapter, decision) {
  if (decision.actionType === ACTION_TYPE.SELECT_OPTION) {
    return adapter.selectOption(decision.locator, decision.value);
  }
  if (decision.actionType === ACTION_TYPE.CHECK_BOX) {
    return adapter.check(decision.locator);
  }
  if (decision.actionType === ACTION_TYPE.CLICK) {
    return adapter.click(decision.locator);
  }
  if (decision.actionType === ACTION_TYPE.WAIT) {
    await adapter.waitFor(decision.waitMs || 300);
    return "wait";
  }
  return null;
}

function mapTerminalStateToRunStatus(terminalState) {
  if (terminalState === TERMINAL_STATE.SUCCESS || terminalState === TERMINAL_STATE.ALREADY_REQUESTED) {
    return RUN_STATUS.COMPLETED;
  }
  if (
    terminalState === TERMINAL_STATE.MANUAL_REVIEW_REQUIRED ||
    terminalState === TERMINAL_STATE.BLOCKED_BY_VALIDATION
  ) {
    return RUN_STATUS.BLOCKED;
  }
  return RUN_STATUS.FAILED;
}

export async function runScenario({
  workspace,
  scenario,
  baseUrl,
  requestContext,
  headless = true,
  maxSteps = 12
}) {
  const { paths, state } = await startRun({
    workspace,
    scenario,
    goal: `Run controlled benchmark scenario: ${scenario}`,
    requestContext
  });

  const browser = await chromium.launch({ headless });
  const page = await browser.newPage();
  const adapter = createBrowserAdapter(page);

  try {
    await adapter.gotoRequestPage(baseUrl, scenario);

    for (let stepIndex = 1; stepIndex <= maxSteps; stepIndex += 1) {
      const stepId = `S${String(stepIndex).padStart(3, "0")}`;
      const observation = await captureObservation(page, adapter, {
        screenshotDir: paths.screenshotDir,
        stepId
      });
      const decision = decideNextAction(requestContext, observation);

      if (decision.terminal) {
        await recordEvent(paths, {
          state,
          stepId,
          status: decision.state,
          summary: decision.reason,
          observation,
          decision
        });
        await finalizeRun(paths, state, {
          status: mapTerminalStateToRunStatus(decision.state),
          summary: decision.reason,
          observation,
          nextAction: {
            action: "Stop and review the terminal benchmark state.",
            reason: decision.reason,
            terminalState: decision.state
          }
        });
        return {
          scenario,
          terminalState: decision.state,
          state,
          artifacts: paths
        };
      }

      const locatorStrategy = await executeDecision(adapter, decision);
      await adapter.waitFor(150);
      await recordEvent(paths, {
        state,
        stepId,
        status: "progress",
        summary: decision.reason,
        observation,
        decision: {
          ...decision,
          locatorStrategy
        }
      });
    }

    const observation = await captureObservation(page, adapter, {
      screenshotDir: paths.screenshotDir,
      stepId: "S999"
    });
    await finalizeRun(paths, state, {
      status: RUN_STATUS.FAILED,
      summary: "The benchmark exceeded the maximum step limit without reaching a supported terminal state.",
      observation,
      nextAction: {
        action: "Inspect the latest observation and update the policy before retrying.",
        reason: "The run exceeded the maximum step limit.",
        terminalState: TERMINAL_STATE.UNKNOWN_STATE
      }
    });
    return {
      scenario,
      terminalState: TERMINAL_STATE.UNKNOWN_STATE,
      state,
      artifacts: paths
    };
  } finally {
    await page.close();
    await browser.close();
  }
}
