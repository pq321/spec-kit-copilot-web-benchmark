import { test, expect } from "@playwright/test";
import { mkdir, mkdtemp, readFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { runScenario } from "../../src/benchmark/runner.js";
import { BENCHMARK_SCENARIOS, buildScenarioRequestContext } from "../../src/benchmark/scenarios.js";

for (const scenario of BENCHMARK_SCENARIOS) {
  test(`${scenario.name} reaches the expected terminal state twice`, async ({ baseURL }, testInfo) => {
    for (const attempt of [1, 2]) {
      await mkdir(testInfo.outputDir, { recursive: true });
      const workspace = await mkdtemp(
        path.join(testInfo.outputDir, `${scenario.name}-${attempt}-`)
      );

      const result = await runScenario({
        workspace,
        scenario: scenario.name,
        baseUrl: baseURL,
        requestContext: buildScenarioRequestContext(scenario.name),
        headless: true
      });

      expect(result.terminalState).toBe(scenario.expectedTerminalState);

      const stateFile = JSON.parse(
        await readFile(path.join(workspace, ".copilot-agent-kit", "state", "run-state.txton"), "utf8")
      );
      const nextAction = JSON.parse(
        await readFile(path.join(workspace, ".copilot-agent-kit", "queue", "next-action.txton"), "utf8")
      );
      const summary = await readFile(
        path.join(workspace, ".copilot-agent-kit", "artifacts", "last-summary.md"),
        "utf8"
      );

      expect(stateFile.stepsRecorded).toBeGreaterThan(0);
      expect(nextAction.terminalState).toBe(scenario.expectedTerminalState);
      expect(summary).toContain("Recent Events");
    }
  });
}
