"""Normalize chat transcripts into JSONL evaluation samples."""

import json
import re
from typing import Any, Dict, List


ROLE_LINE = re.compile(r"^\s*(user|human|assistant|ai|system|tool)(?:\s*\(([^)]*)\))?\s*:\s*(.*)$", re.I)


def _normalize_messages(source: Any) -> List[Dict[str, Any]]:
    if isinstance(source, list):
        messages = source
    elif isinstance(source, str):
        value = source.strip()
        if not value:
            raise ValueError("Conversation cannot be empty")
        if value.startswith("["):
            try:
                messages = json.loads(value)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid messages JSON: {exc}") from exc
            if not isinstance(messages, list):
                raise ValueError("Messages JSON must be an array")
        else:
            messages = []
            for line in value.splitlines():
                match = ROLE_LINE.match(line)
                if match:
                    role = match.group(1).lower()
                    role = {"human": "user", "ai": "assistant"}.get(role, role)
                    messages.append({"role": role, "content": match.group(3)})
                elif messages:
                    messages[-1]["content"] = str(messages[-1].get("content", "")) + "\n" + line
            if not messages:
                messages = [{"role": "user", "content": value}]
    else:
        raise ValueError("Conversation must be text or an array of messages")
    normalized: List[Dict[str, Any]] = []
    for item in messages:
        if not isinstance(item, dict) or "role" not in item:
            continue
        role = str(item["role"]).lower()
        content = item.get("content", "")
        if isinstance(content, (dict, list)):
            content = json.dumps(content, ensure_ascii=False)
        normalized.append({"role": role, "content": str(content), **({"tool_call": item["tool_call"]} if "tool_call" in item else {})})
    if not normalized:
        raise ValueError("No valid messages found")
    return normalized


def build_agent_dataset(source: Any) -> Dict[str, Any]:
    messages = _normalize_messages(source)
    samples: List[Dict[str, Any]] = []
    for index, message in enumerate(messages):
        if message["role"] != "user":
            continue
        answer = next((m for m in messages[index + 1 :] if m["role"] == "assistant"), None)
        tools = [m for m in messages[index + 1 :] if m["role"] == "tool"]
        sample = {"id": f"sample-{len(samples) + 1:03d}", "input": message["content"], "expected_output": answer["content"] if answer else "", "metadata": {"source_index": index}}
        if tools:
            sample["tool_calls"] = [m["content"] for m in tools]
        samples.append(sample)
    jsonl = "\n".join(json.dumps(sample, ensure_ascii=False) for sample in samples)
    return {"messages": messages, "samples": samples, "jsonl": jsonl, "count": len(samples), "format": "devconvert-agent-eval-v1"}
