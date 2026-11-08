import copy
import json
from pathlib import Path

from .base import LLMResponse, ModelUnavailable, ToolCall


class ScriptedMockLLM:
    """Replays fixture rounds. Never reads observations; no model decision evidence."""

    metadata = {"mode": "mock", "provider": "offline", "model": "scripted-mock",
                "temperature": 0, "decision_evidence": False}

    def __init__(self, script):
        if isinstance(script, (str, Path)):
            script = json.loads(Path(script).read_text(encoding="utf-8-sig"))
        self.script = copy.deepcopy(script)
        self.index = 0

    def chat(self, messages, tools):
        # messages/tools deliberately unused: this is a fixed script, not a policy agent.
        if self.index >= len(self.script):
            raise ModelUnavailable("MOCK_SCRIPT_EXHAUSTED")
        round_ = self.script[self.index]
        self.index += 1
        calls = [ToolCall(f"mock-{self.index}-{i}", c["name"], c["arguments"])
                 for i, c in enumerate(round_.get("calls", []), 1)]
        return LLMResponse(calls, round_.get("content"))
