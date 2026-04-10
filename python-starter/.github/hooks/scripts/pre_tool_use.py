from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone


DANGEROUS_PATTERNS = ("rm -rf", "git reset --hard", "del /f /s /q")


def main() -> None:
    raw = os.environ.get("COPILOT_TOOL_INPUT", "")
    record = {
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "hook": "PreToolUse",
        "toolInput": raw
    }
    if any(pattern in raw for pattern in DANGEROUS_PATTERNS):
        record["blocked"] = True
        record["reason"] = "Blocked dangerous command pattern."
        with open(".copilot-agent-kit/logs/hook-events.jsonl", "a", encoding="utf-8") as handle:
            json.dump(record, handle, ensure_ascii=False)
            handle.write("\n")
        sys.exit(2)
    record["blocked"] = False
    with open(".copilot-agent-kit/logs/hook-events.jsonl", "a", encoding="utf-8") as handle:
        json.dump(record, handle, ensure_ascii=False)
        handle.write("\n")


if __name__ == "__main__":
    main()
