from types import SimpleNamespace

import httpx
import pytest
from openai import OpenAI

from schedule_agent.config import ModelConfig
from schedule_agent.llm.openai_compat import OpenAICompatClient
from schedule_agent.llm.base import ModelUnavailable


def test_live_adapter_serializes_real_sdk_protocol_without_network():
    requests = []
    def handler(request):
        requests.append(request)
        return httpx.Response(200, json={"id": "chat-test", "object": "chat.completion", "created": 0,
            "model": "provider-returned-model", "choices": [{"index": 0, "finish_reason": "tool_calls",
            "message": {"role": "assistant", "content": None, "tool_calls": [{"id": "call-1", "type": "function",
                "function": {"name": "get_material", "arguments": "{broken"}}]}}],
            "usage": {"prompt_tokens": 42, "completion_tokens": 7, "total_tokens": 49}})
    client = OpenAI(base_url="https://offline.invalid/v1", api_key="offline-test-placeholder",
                    http_client=httpx.Client(transport=httpx.MockTransport(handler)))
    adapter = OpenAICompatClient(ModelConfig("https://offline.invalid/v1", "unused", "configured-model"), client)
    response = adapter.chat([{"role": "user", "content": "test"}], [])
    assert response.usage == {"prompt_tokens": 42, "completion_tokens": 7}
    assert response.model == "provider-returned-model"
    assert response.tool_calls[0].arguments == "{broken"
    assert requests[0].url.path == "/v1/chat/completions"
    client.close()


def test_model_http_errors_never_expose_secrets():
    client = OpenAI(base_url="https://offline.invalid", api_key="offline-test-placeholder", max_retries=0,
        http_client=httpx.Client(transport=httpx.MockTransport(lambda req: httpx.Response(401, json={"error": {"message": "secret-in-error"}}))))
    adapter = OpenAICompatClient(ModelConfig("https://offline.invalid", "unused", "test"), client)
    with pytest.raises(ModelUnavailable) as exc:
        adapter.chat([], [])
    assert "secret-in-error" not in str(exc.value)
    client.close()
