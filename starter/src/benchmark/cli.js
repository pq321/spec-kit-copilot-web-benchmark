import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";
import { startServer } from "../../site/server.js";
import { runScenario } from "./runner.js";
import { buildScenarioRequestContext } from "./scenarios.js";

function parseArgs(argv) {
  const args = {};
  for (let index = 0; index < argv.length; index += 1) {
    const entry = argv[index];
    if (!entry.startsWith("--")) {
      continue;
    }
    const key = entry.slice(2);
    const next = argv[index + 1];
    if (!next || next.startsWith("--")) {
      args[key] = true;
    } else {
      args[key] = next;
      index += 1;
    }
  }
  return args;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const scenario = args.scenario || "normal";
  const workspace = path.resolve(args.workspace || process.cwd());
  const headless = args.headed ? false : true;

  let serverHandle = null;
  let baseUrl = args["base-url"];

  if (!baseUrl) {
    serverHandle = await startServer();
    baseUrl = serverHandle.url;
  }

  try {
    const result = await runScenario({
      workspace,
      scenario,
      baseUrl,
      requestContext: buildScenarioRequestContext(scenario),
      headless
    });
    process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
  } finally {
    if (serverHandle?.server) {
      await new Promise((resolve) => serverHandle.server.close(resolve));
    }
  }
}

const currentFile = fileURLToPath(import.meta.url);
if (process.argv[1] === currentFile) {
  main().catch((error) => {
    process.stderr.write(`${error instanceof Error ? error.stack : String(error)}\n`);
    process.exitCode = 1;
  });
}
