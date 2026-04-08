export const LOCATOR_STRATEGY_ORDER = Object.freeze([
  "role",
  "label",
  "text",
  "testId",
  "css",
  "xpath"
]);

export const RUN_STATUS = Object.freeze({
  ACTIVE: "active",
  COMPLETED: "completed",
  BLOCKED: "blocked",
  FAILED: "failed"
});

export const TERMINAL_STATE = Object.freeze({
  SUCCESS: "success",
  ALREADY_REQUESTED: "already_requested",
  MANUAL_REVIEW_REQUIRED: "manual_approval_required",
  BLOCKED_BY_VALIDATION: "blocked_by_validation",
  UNKNOWN_STATE: "unknown_state"
});

export const ACTION_TYPE = Object.freeze({
  SELECT_OPTION: "select_option",
  CHECK_BOX: "check_box",
  CLICK: "click",
  WAIT: "wait",
  TERMINAL: "terminal"
});

export const SCENARIO_EXPECTATIONS = Object.freeze({
  normal: TERMINAL_STATE.SUCCESS,
  already_requested: TERMINAL_STATE.ALREADY_REQUESTED,
  prerequisite_unlock: TERMINAL_STATE.SUCCESS,
  ambiguous_locator: TERMINAL_STATE.SUCCESS,
  dynamic_dom: TERMINAL_STATE.SUCCESS,
  manual_review: TERMINAL_STATE.MANUAL_REVIEW_REQUIRED,
  failure_recovery: TERMINAL_STATE.SUCCESS
});

export function createRequestContext(overrides = {}) {
  return {
    scenario: overrides.scenario || "normal",
    targetSystem: overrides.targetSystem || "Payroll Portal",
    targetPackage: overrides.targetPackage || "Finance Reporter",
    targetPermission: overrides.targetPermission || "View Reports",
    accountName: overrides.accountName || "benchmark.user@example.com",
    environment: overrides.environment || "benchmark",
    approvalMode: overrides.approvalMode || "auto-when-possible"
  };
}
