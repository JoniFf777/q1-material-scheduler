from urllib.parse import urlparse

from openai import OpenAI, OpenAIError

from .base import LLMResponse, ModelUnavailable, ToolCall


class OpenAICompatClient:
    def __init__(self, config, client=None):
        self.model = config.model
        host = urlparse(config.base_url).hostname or "custom"
        self.metadata = {"mode": "live", "provider": host, "model": self.model, "temperature": 0}
        self.client = client or OpenAI(base_url=config.base_url, api_key=config.api_key,
                                       timeout=60, max_retries=2)

    def chat(self, messages, tools):
        try:
            response = self.client.chat.completions.create(model=self.model, messages=messages,
                tools=tools, tool_choice="auto", temperature=0)
        except OpenAIError as exc:
            raise ModelUnavailable(type(exc).__name__) from None
        if not response.choices:
            raise ModelUnavailable("EMPTY_MODEL_RESPONSE")
        message = response.choices[0].message
        calls = [ToolCall(c.id, c.function.name, c.function.arguments)
                 for c in message.tool_calls or [] if c.type == "function"]
        usage = response.usage
        return LLMResponse(calls, message.content,
            {"prompt_tokens": usage.prompt_tokens if usage else 0,
             "completion_tokens": usage.completion_tokens if usage else 0}, response.model)
