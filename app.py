"""DevConvert backend API.

The service intentionally keeps the API surface small: each endpoint accepts one
JSON payload and returns deterministic text/JSON that the browser can download.
"""

from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Union

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from tool_modules.agent_jsonl import build_agent_dataset
from tool_modules.curl_converter import convert_curl
from tool_modules.json_types import convert_json_types
from tool_modules.log_analyzer import analyze_logs


app = FastAPI(title="DevConvert API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CurlPayload(BaseModel):
    curl: str = Field(..., min_length=1, max_length=100_000)
    redact_secrets: bool = True


class JsonTypesPayload(BaseModel):
    # A JSON string is convenient for a textarea, while an object is useful for
    # callers that already parsed the request body.
    json_data: Union[str, Dict[str, Any], List[Any]] = Field(..., alias="json")
    root_name: str = Field("Root", min_length=1, max_length=80)


class LogsPayload(BaseModel):
    text: Optional[str] = Field(None, min_length=1, max_length=2_000_000)
    logs: Optional[str] = Field(None, min_length=1, max_length=2_000_000)
    log: Optional[str] = Field(None, min_length=1, max_length=2_000_000)

    @property
    def content(self) -> str:
        value = self.text or self.logs or self.log
        if not value:
            raise ValueError("Provide text, logs, or log")
        return value


class AgentPayload(BaseModel):
    # Accept `conversation` (the documented name), plus `messages` for clients
    # that use OpenAI's native shape.
    conversation: Optional[Union[str, List[Dict[str, Any]]]] = None
    messages: Optional[List[Dict[str, Any]]] = None


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "service": "devconvert"}


@app.post("/api/convert/curl")
def curl_endpoint(payload: CurlPayload) -> Dict[str, Any]:
    try:
        return convert_curl(payload.curl, redact_secrets=payload.redact_secrets)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/convert/json-types")
def json_types_endpoint(payload: JsonTypesPayload) -> Dict[str, Any]:
    try:
        return convert_json_types(payload.json_data, root_name=payload.root_name)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/analyze/logs")
def logs_endpoint(payload: LogsPayload) -> Dict[str, Any]:
    try:
        return analyze_logs(payload.content)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/convert/agent-jsonl")
def agent_endpoint(payload: AgentPayload) -> Dict[str, Any]:
    source: Any = payload.messages if payload.messages is not None else payload.conversation
    if source is None:
        raise HTTPException(status_code=422, detail="Provide conversation or messages")
    try:
        return build_agent_dataset(source)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


# The frontend can be served by a separate dev server. If a static directory is
# present in a packaged deployment, mounting it here makes the API self-hosting.
runtime_root = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
static_dir = runtime_root / "static"
if static_dir.is_dir():
    from fastapi.staticfiles import StaticFiles

    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(static_dir / "index.html")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False)
