import test from "node:test";
import assert from "node:assert/strict";
import { buildLocatorPlan } from "../../src/benchmark/browser-adapter.js";
import { decideNextAction, detectPageState } from "../../src/benchmark/policy.js";
import { ACTION_TYPE, TERMINAL_STATE, createRequestContext } from "../../src/benchmark/types.js";

function observation(overrides = {}) {
  return {
    url: "http://127.0.0.1/request.html?scenario=test",
    title: "Permission Request Workflow",
    headings: [],
    banners: [],
    domEvidence: "",
    screenshotPath: "artifact.png",
    controls: [],
    ...overrides
  };
}

test("buildLocatorPlan keeps semantic locator priority ahead of xpath", () => {
  const plan = buildLocatorPlan({
    role: "button",
    name: "Next",
    label: "Next",
    text: "Next",
    testId: "workflow-next",
    css: "#workflow-next-button",
    xpath: "//button[text()='Next']"
  });

  assert.deepEqual(plan, ["role", "label", "text", "testId", "css", "xpath"]);
});

test("detectPageState identifies already requested terminal state", () => {
  const state = detectPageState(
    observation({
      banners: ["Request already exists for this permission."]
    })
  );

  assert.equal(state, TERMINAL_STATE.ALREADY_REQUESTED);
});

test("decideNextAction selects the system before clicking next", () => {
  const requestContext = createRequestContext();
  const decision = decideNextAction(
    requestContext,
    observation({
      headings: ["Step 1: Choose a system"],
      controls: [
        {
          role: "combobox",
          label: "System",
          text: "",
          disabled: false,
          value: "",
          checked: false
        }
      ]
    })
  );

  assert.equal(decision.actionType, ACTION_TYPE.SELECT_OPTION);
  assert.equal(decision.value, requestContext.targetSystem);
});

test("decideNextAction escalates when permission remains disabled", () => {
  const requestContext = createRequestContext();
  const decision = decideNextAction(
    requestContext,
    observation({
      headings: ["Step 2: Choose access package"],
      controls: [
        {
          role: "combobox",
          label: "Access package",
          text: "",
          disabled: false,
          value: requestContext.targetPackage,
          checked: false
        },
        {
          role: "combobox",
          label: "Permission",
          text: "",
          disabled: true,
          value: "",
          checked: false
        }
      ]
    })
  );

  assert.equal(decision.terminal, true);
  assert.equal(decision.state, TERMINAL_STATE.BLOCKED_BY_VALIDATION);
});
