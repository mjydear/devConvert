"""Parse cURL snippets and generate equivalent client code."""

import json
import re
import shlex
from typing import Any, Dict, List, Tuple
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


SENSITIVE = re.compile(r"^(authorization|proxy-authorization|cookie|set-cookie|x-api-key|.*token.*|.*secret.*)$", re.I)


def _mask(value: str) -> str:
    if not value:
        return "***"
    if value.lower().startswith("bearer "):
        return "Bearer ***"
    return "***"


def _tokens(command: str) -> List[str]:
    command = command.strip()
    command = re.sub(r"^\s*\$\s+", "", command)
    # Browser snippets often have line continuations.
    command = command.replace("\\\n", " ").replace("^\n", " ")
    try:
        return shlex.split(command, posix=True)
    except ValueError as exc:
        raise ValueError(f"Unable to parse cURL quoting: {exc}") from exc


def _header_pair(raw: str) -> Tuple[str, str]:
    if ":" not in raw:
        raise ValueError(f"Invalid header (expected Name: value): {raw}")
    key, value = raw.split(":", 1)
    key = key.strip()
    if not key:
        raise ValueError("Header name cannot be empty")
    return key, value.strip()


def _quote_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def _code(method: str, url: str, headers: Dict[str, str], body: Any) -> Dict[str, str]:
    body_json = _quote_json(body) if body is not None else None
    fetch_lines = [f"const response = await fetch({json.dumps(url)}, {{", f"  method: {json.dumps(method)},"]
    if headers:
        fetch_lines.append("  headers: " + json.dumps(headers, ensure_ascii=False) + ",")
    if body_json is not None:
        fetch_lines.append("  body: " + json.dumps(body_json, ensure_ascii=False) + ",")
    fetch_lines += ["});", "const data = await response.json();"]

    axios = [f"const response = await axios.{method.lower()}({json.dumps(url)}"]
    if body_json is not None:
        axios.append(", " + body_json.replace("\n", "\n  "))
    elif headers:
        axios.append(", undefined")
    if headers:
        axios.append(", { headers: " + json.dumps(headers, ensure_ascii=False) + " }")
    axios.append(");")

    py = ["import requests", "", f"response = requests.request(", f"    {method!r},", f"    {url!r},"]
    if headers:
        py.append(f"    headers={headers!r},")
    if body is not None:
        py.append(f"    json={body!r},")
    py += [")", "data = response.json()"]

    java = [
        "var client = java.net.http.HttpClient.newHttpClient();",
        "var request = java.net.http.HttpRequest.newBuilder()",
        f"    .uri(java.net.URI.create({json.dumps(url)}))",
    ]
    for key, value in headers.items():
        java.append(f"    .header({json.dumps(key)}, {json.dumps(value)})")
    if body_json is None:
        java.append(f"    .method({json.dumps(method)}, java.net.http.HttpRequest.BodyPublishers.noBody())")
    else:
        java.append(f"    .method({json.dumps(method)}, java.net.http.HttpRequest.BodyPublishers.ofString({json.dumps(body_json)}))")
    java += ["    .build();", "var response = client.send(request, java.net.http.HttpResponse.BodyHandlers.ofString());"]
    return {"fetch": "\n".join(fetch_lines), "axios": "\n".join(axios), "python": "\n".join(py), "java": "\n".join(java)}


def convert_curl(command: str, redact_secrets: bool = True) -> Dict[str, Any]:
    tokens = _tokens(command)
    if not tokens or tokens[0].lower() != "curl":
        raise ValueError("Input must be a cURL command")
    method = "GET"
    headers: Dict[str, str] = {}
    body_raw: str | None = None
    url = ""
    get_mode = False
    i = 1
    while i < len(tokens):
        token = tokens[i]
        if token in ("-X", "--request"):
            i += 1
            if i >= len(tokens):
                raise ValueError("Missing method after --request")
            method = tokens[i].upper()
        elif token.startswith("--request="):
            method = token.split("=", 1)[1].upper()
        elif token in ("-H", "--header"):
            i += 1
            if i >= len(tokens):
                raise ValueError("Missing value after --header")
            key, value = _header_pair(tokens[i])
            headers[key] = value
        elif token.startswith("--header="):
            key, value = _header_pair(token.split("=", 1)[1])
            headers[key] = value
        elif token in ("-d", "--data", "--data-raw", "--data-binary", "--data-urlencode"):
            i += 1
            if i >= len(tokens):
                raise ValueError("Missing body after --data")
            body_raw = tokens[i]
            if method == "GET":
                method = "POST"
        elif token in ("-G", "--get"):
            get_mode = True
            method = "GET"
        elif token in ("--url",):
            i += 1
            if i >= len(tokens):
                raise ValueError("Missing URL after --url")
            url = tokens[i]
        elif token.startswith("http://") or token.startswith("https://"):
            url = token
        elif not token.startswith("-") and not url:
            url = token
        i += 1
    if not url:
        raise ValueError("No URL found in cURL command")

    body: Any = body_raw
    content_type = next((v for k, v in headers.items() if k.lower() == "content-type"), "")
    if body_raw is not None and ("json" in content_type.lower() or body_raw.lstrip().startswith(("{", "["))):
        try:
            body = json.loads(body_raw)
        except json.JSONDecodeError:
            body = body_raw
    if get_mode and body_raw:
        parts = urlsplit(url)
        query = parse_qsl(parts.query, keep_blank_values=True) + parse_qsl(body_raw, keep_blank_values=True)
        url = urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))
        body = None

    original_headers = dict(headers)
    if redact_secrets:
        headers = {k: (_mask(v) if SENSITIVE.match(k) else v) for k, v in headers.items()}
    query_params = dict(parse_qsl(urlsplit(url).query, keep_blank_values=True))
    return {
        "method": method,
        "url": url,
        "headers": headers,
        "query": query_params,
        "body": body,
        "redacted": redact_secrets and headers != original_headers,
        "code": _code(method, url, headers, body),
    }
