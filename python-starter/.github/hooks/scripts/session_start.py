from __future__ import annotations

import json
import os
from datetime import datetime, timezone


def main() -> None:
    os.makedirs(".copilot-agent-kit/logs", exist_ok=True)
    record = {
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "hook": "SessionStart",
        "summary": "Session started. Load run-state and site runbook before acting."
    }
    with open(".copilot-agent-kit/logs/hook-events.jsonl", "a", encoding="utf-8") as handle:
        json.dump(record, handle, ensure_ascii=False)
        handle.write("\n")


if __name__ == "__main__":
    main()
