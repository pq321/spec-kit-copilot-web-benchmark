import { SCENARIO_EXPECTATIONS, createRequestContext } from "./types.js";

export const BENCHMARK_SCENARIOS = Object.freeze(
  Object.keys(SCENARIO_EXPECTATIONS).map((name) => ({
    name,
    expectedTerminalState: SCENARIO_EXPECTATIONS[name]
  }))
);

export function buildScenarioRequestContext(scenario, overrides = {}) {
  return createRequestContext({
    scenario,
    ...overrides
  });
}
