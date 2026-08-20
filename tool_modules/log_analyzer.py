"""Small, dependency-free log and stack trace analyzer."""

import re
from collections import Counter, defaultdict
from typing import Any, Dict, List


LEVEL_RE = re.compile(r"\b(TRACE|DEBUG|INFO|NOTICE|WARN(?:ING)?|ERROR|FATAL|CRITICAL)\b", re.I)
TIME_RE = re.compile(r"(?:^|[\[\s])(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)")
EXC_RE = re.compile(r"\b([A-Za-z_$][\w$]*(?:Exception|Error|Failure))\b")
FRAME_RE = re.compile(r"(?:at\s+)?([\w.$<>]+\([^)]*\)|[\w./-]+:\d+(?::\d+)?)")


def analyze_logs(text: str) -> Dict[str, Any]:
    lines = text.splitlines()
    level_counts: Counter[str] = Counter()
    hour_counts: Counter[str] = Counter()
    errors: List[Dict[str, Any]] = []
    groups: Dict[str, Dict[str, Any]] = {}
    current: Dict[str, Any] | None = None

    def finish() -> None:
        nonlocal current
        if current is None:
            return
        message = current["message"]
        key = f"{current.get('exception') or current['level']}::{re.sub(r'\\d+', '#', message)[:180]}"
        group = groups.setdefault(key, {"signature": key.split("::", 1)[1], "count": 0, "level": current["level"], "example_line": current["line"]})
        group["count"] += 1
        if len(errors) < 200:
            errors.append(current)
        current = None

    for line_no, line in enumerate(lines, 1):
        level_match = LEVEL_RE.search(line)
        level = level_match.group(1).upper() if level_match else "UNKNOWN"
        if level == "WARNING":
            level = "WARN"
        time_match = TIME_RE.search(line)
        timestamp = time_match.group(1) if time_match else None
        if timestamp:
            hour_counts[timestamp[:13].replace("T", " ")] += 1
        if level not in ("UNKNOWN",):
            level_counts[level] += 1
        is_error = level in {"ERROR", "FATAL", "CRITICAL"} or bool(EXC_RE.search(line))
        continuation = bool(current and (line.startswith((" ", "\t")) or line.lstrip().startswith(("at ", "Caused by:"))))
        if is_error and not continuation:
            finish()
            exception = EXC_RE.search(line)
            current = {"line": line_no, "level": level, "timestamp": timestamp, "message": line.strip(), "exception": exception.group(1) if exception else None, "stack": []}
        elif current and continuation:
            frame = FRAME_RE.search(line)
            if frame and len(current["stack"]) < 12:
                current["stack"].append(frame.group(1))
        elif current and not continuation:
            finish()
    finish()
    sorted_groups = sorted(groups.values(), key=lambda item: item["count"], reverse=True)
    return {
        "summary": {"lines": len(lines), "levels": dict(level_counts), "timestamps": dict(hour_counts), "error_count": len(errors), "unique_errors": len(groups)},
        "errors": errors,
        "error_groups": sorted_groups,
    }
