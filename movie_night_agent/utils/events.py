# utils/events.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ToolCall:
    tool_name: str
    args: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolOutput:
    tool_name: str
    output: Any


@dataclass
class RunResult:
    final_text: Optional[str] = None
    text_chunks: List[str] = field(default_factory=list)
    tool_calls: List[ToolCall] = field(default_factory=list)
    tool_outputs: List[ToolOutput] = field(default_factory=list)
    authors: List[str] = field(default_factory=list)


def _safe_get(obj: Any, attr: str, default=None):
    return getattr(obj, attr, default)


def extract_from_event(event) -> Dict[str, Any]:
    """
    Normalize an ADK event into:
      - texts
      - tool_calls (function_call parts)
      - tool_outputs (tool_response parts)
    """
    extracted = {"texts": [], "tool_calls": [], "tool_outputs": []}

    content = _safe_get(event, "content", None)
    parts = _safe_get(content, "parts", None) or []

    for part in parts:
        # text chunks
        text = _safe_get(part, "text", None)
        if text and not text.isspace():
            extracted["texts"].append(text.strip())

        # tool response
        tool_response = _safe_get(part, "tool_response", None)
        if tool_response:
            name = _safe_get(tool_response, "name", "unknown_tool")
            output = _safe_get(tool_response, "output", None)
            extracted["tool_outputs"].append({"tool_name": name, "output": output})

        # function/tool call
        function_call = _safe_get(part, "function_call", None)
        if function_call:
            name = _safe_get(function_call, "name", "unknown_function")
            args = _safe_get(function_call, "args", {}) or {}
            extracted["tool_calls"].append({"tool_name": name, "args": args})

    return extracted


def accumulate_result(result: RunResult, event) -> None:
    author = _safe_get(event, "author", None)
    if author:
        result.authors.append(author)

    extracted = extract_from_event(event)

    for t in extracted["texts"]:
        result.text_chunks.append(t)

    for c in extracted["tool_calls"]:
        result.tool_calls.append(ToolCall(**c))

    for o in extracted["tool_outputs"]:
        result.tool_outputs.append(ToolOutput(**o))

    if event.is_final_response() and extracted["texts"]:
        result.final_text = extracted["texts"][0]
