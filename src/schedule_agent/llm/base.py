import json
from dataclasses import dataclass, field
from typing import Protocol


class ModelUnavailable(RuntimeError):
    """Sanitized transport error: never embed credentials or response bodies."""


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict | str

    def message(self):
        return {"id": self.id, "type": "function", "function": {
            "name": self.name, "arguments": self.arguments if isinstance(self.arguments, str)
            else json.dumps(self.arguments, ensure_ascii=False)}}


@dataclass
class LLMResponse:
    tool_calls: list[ToolCall] = field(default_factory=list)
    content: str | None = None
    usage: dict = field(default_factory=lambda: {"prompt_tokens": 0, "completion_tokens": 0})
    model: str | None = None

    def message(self):
        result = {"role": "assistant", "content": self.content}
        if self.tool_calls:
            result["tool_calls"] = [call.message() for call in self.tool_calls]
        return result


class LLMClient(Protocol):
    metadata: dict

    def chat(self, messages: list, tools: list) -> LLMResponse: ...
