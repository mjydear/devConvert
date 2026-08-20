"""JSON to TypeScript and JSON Schema conversion."""

import json
import re
from typing import Any, Dict, List


def _name(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_$]", "_", value)
    if not value or value[0].isdigit():
        value = "Type_" + value
    return value


def _ts_type(value: Any, name: str, interfaces: List[str]) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int) and not isinstance(value, bool):
        return "number"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, dict):
        interface_name = _name(name)
        lines = [f"export interface {interface_name} {{"]
        for key, child in value.items():
            prop = key if re.match(r"^[A-Za-z_$][\w$]*$", key) else json.dumps(key, ensure_ascii=False)
            lines.append(f"  {prop}: {_ts_type(child, interface_name + _name(str(key).title()), interfaces)};")
        lines.append("}")
        interfaces.append("\n".join(lines))
        return interface_name
    if isinstance(value, list):
        if not value:
            return "unknown[]"
        types = {_ts_type(v, name + "Item", interfaces) for v in value}
        item = next(iter(types)) if len(types) == 1 else " | ".join(sorted(types))
        return f"({item})[]" if " | " in item else f"{item}[]"
    return "unknown"


def _schema(value: Any) -> Dict[str, Any]:
    if value is None:
        return {"type": "null"}
    if isinstance(value, bool):
        return {"type": "boolean"}
    if isinstance(value, int) and not isinstance(value, bool):
        return {"type": "integer"}
    if isinstance(value, float):
        return {"type": "number"}
    if isinstance(value, str):
        return {"type": "string"}
    if isinstance(value, dict):
        return {"type": "object", "properties": {str(k): _schema(v) for k, v in value.items()}, "required": [str(k) for k in value]}
    if isinstance(value, list):
        if not value:
            return {"type": "array", "items": {}}
        item_schemas = [_schema(v) for v in value]
        unique = []
        for schema in item_schemas:
            if schema not in unique:
                unique.append(schema)
        return {"type": "array", "items": unique[0] if len(unique) == 1 else {"anyOf": unique}}
    return {}


def convert_json_types(source: Any, root_name: str = "Root") -> Dict[str, Any]:
    if isinstance(source, str):
        try:
            value = json.loads(source)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON at line {exc.lineno}, column {exc.colno}") from exc
    else:
        value = source
    interfaces: List[str] = []
    root_type = _ts_type(value, _name(root_name), interfaces)
    if isinstance(value, dict):
        typescript = "\n\n".join(reversed(interfaces))
    else:
        typescript = f"export type {_name(root_name)} = {root_type};"
    return {"typescript": typescript, "json_schema": _schema(value), "value": value}
