from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--subagent", action="store_true")
    args = parser.parse_args()

    os.makedirs(".copilot-agent-kit/logs", exist_ok=True)
    record = {
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "hook": "SubagentStop" if args.subagent else "AgentStop",
        "summary": "Agent turn ended. Ensure summary and next action are current."
    }
    with open(".copilot-agent-kit/logs/hook-events.jsonl", "a", encoding="utf-8") as handle:
        json.dump(record, handle, ensure_ascii=False)
        handle.write("\n")


if __name__ == "__main__":
    main()
