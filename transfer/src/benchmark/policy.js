import { ACTION_TYPE, TERMINAL_STATE } from "./types.js";

function hasText(observation, text) {
  const haystack = `${observation.title} ${observation.headings.join(" ")} ${observation.banners.join(" ")} ${observation.domEvidence}`.toLowerCase();
  return haystack.includes(text.toLowerCase());
}

function findControl(observation, predicate) {
  return observation.controls.find(predicate);
}

export function detectPageState(observation) {
  if (hasText(observation, "Request submitted successfully")) {
    return TERMINAL_STATE.SUCCESS;
  }
  if (hasText(observation, "Request already exists")) {
    return TERMINAL_STATE.ALREADY_REQUESTED;
  }
  if (hasText(observation, "Manager approval required")) {
    return TERMINAL_STATE.MANUAL_REVIEW_REQUIRED;
  }
  if (hasText(observation, "Temporary service issue")) {
    return "transient_failure";
  }
  if (hasText(observation, "Unlocking permissions")) {
    return "dynamic_loading";
  }
  if (hasText(observation, "Step 1: Choose a system")) {
    return "step_system";
  }
  if (hasText(observation, "Step 2: Choose access package")) {
    return "step_package";
  }
  if (hasText(observation, "Step 3: Review request")) {
    return "step_review";
  }
  return TERMINAL_STATE.UNKNOWN_STATE;
}

function terminalDecision(state, reason) {
  return {
    state,
    actionType: ACTION_TYPE.TERMINAL,
    reason,
    terminal: true
  };
}

export function decideNextAction(requestContext, observation) {
  const state = detectPageState(observation);

  if (state === TERMINAL_STATE.SUCCESS) {
    return terminalDecision(state, "The benchmark page reports a successful request.");
  }
  if (state === TERMINAL_STATE.ALREADY_REQUESTED) {
    return terminalDecision(state, "The page states that the permission request already exists.");
  }
  if (state === TERMINAL_STATE.MANUAL_REVIEW_REQUIRED) {
    return terminalDecision(state, "The workflow reached a human approval gate.");
  }
  if (state === TERMINAL_STATE.UNKNOWN_STATE) {
    return terminalDecision(state, "The page does not match a supported benchmark state.");
  }

  if (state === "dynamic_loading") {
    return {
      state,
      actionType: ACTION_TYPE.WAIT,
      reason: "The page is still re-rendering the permission controls.",
      terminal: false,
      waitMs: 400
    };
  }

  if (state === "transient_failure") {
    return {
      state,
      actionType: ACTION_TYPE.CLICK,
      reason: "The page indicates a transient failure and a retry submit is available.",
      terminal: false,
      locator: {
        scope: "main",
        role: "button",
        name: "Retry submit",
        text: "Retry submit",
        testId: "submit-request",
        css: "#submit-request-button"
      }
    };
  }

  if (state === "step_system") {
    const systemSelect = findControl(
      observation,
      (control) => control.role === "combobox" && control.label === "System"
    );
    if (!systemSelect?.value) {
      return {
        state,
        actionType: ACTION_TYPE.SELECT_OPTION,
        reason: "The system is not selected yet.",
        terminal: false,
        locator: {
          scope: "main",
          label: "System",
          testId: "system-select",
          css: "#system-select"
        },
        value: requestContext.targetSystem
      };
    }
    return {
      state,
      actionType: ACTION_TYPE.CLICK,
      reason: "The system is selected, so the workflow can continue.",
      terminal: false,
      locator: {
        scope: "main",
        role: "button",
        name: "Next",
        text: "Next",
        testId: "workflow-next",
        css: "#workflow-next-button"
      }
    };
  }

  if (state === "step_package") {
    const packageSelect = findControl(
      observation,
      (control) => control.role === "combobox" && control.label === "Access package"
    );
    const permissionSelect = findControl(
      observation,
      (control) => control.role === "combobox" && control.label === "Permission"
    );
    const acknowledgement = findControl(
      observation,
      (control) => control.role === "checkbox" && control.label.includes("Acknowledge production access")
    );

    if (!packageSelect?.value) {
      return {
        state,
        actionType: ACTION_TYPE.SELECT_OPTION,
        reason: "The access package must be selected before continuing.",
        terminal: false,
        locator: {
          scope: "main",
          label: "Access package",
          testId: "package-select",
          css: "#package-select"
        },
        value: requestContext.targetPackage
      };
    }

    if (acknowledgement && !acknowledgement.checked) {
      return {
        state,
        actionType: ACTION_TYPE.CHECK_BOX,
        reason: "The production prerequisite checkbox is required to unlock permissions.",
        terminal: false,
        locator: {
          scope: "main",
          label: "Acknowledge production access",
          testId: "production-ack",
          css: "#production-ack"
        }
      };
    }

    if (permissionSelect?.disabled) {
      return terminalDecision(
        TERMINAL_STATE.BLOCKED_BY_VALIDATION,
        "Permission selection is still disabled after the expected prerequisites."
      );
    }

    if (!permissionSelect?.value) {
      return {
        state,
        actionType: ACTION_TYPE.SELECT_OPTION,
        reason: "A permission must be selected before proceeding to review.",
        terminal: false,
        locator: {
          scope: "main",
          label: "Permission",
          testId: "permission-select",
          css: "#permission-select"
        },
        value: requestContext.targetPermission
      };
    }

    return {
      state,
      actionType: ACTION_TYPE.CLICK,
      reason: "The package and permission are selected, so the workflow can continue.",
      terminal: false,
      locator: {
        scope: "main",
        role: "button",
        name: "Next",
        text: "Next",
        testId: "workflow-next",
        css: "#workflow-next-button"
      }
    };
  }

  if (state === "step_review") {
    const submitButton = findControl(
      observation,
      (control) => control.role === "button" && control.text.toLowerCase().includes("submit")
    );

    if (submitButton?.disabled) {
      return terminalDecision(
        TERMINAL_STATE.BLOCKED_BY_VALIDATION,
        "The submit button is disabled and the page does not expose a valid forward path."
      );
    }

    return {
      state,
      actionType: ACTION_TYPE.CLICK,
      reason: "The request is ready for submission.",
      terminal: false,
      locator: {
        scope: "main",
        role: "button",
        name: /submit/i,
        text: "Submit request",
        testId: "submit-request",
        css: "#submit-request-button"
      }
    };
  }

  return terminalDecision(TERMINAL_STATE.UNKNOWN_STATE, "No policy rule matched the current page.");
}
