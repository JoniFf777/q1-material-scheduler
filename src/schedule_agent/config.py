import os
from dataclasses import dataclass, field

from dotenv import load_dotenv


@dataclass(frozen=True)
class ModelConfig:
    base_url: str
    api_key: str = field(repr=False)
    model: str = ""

    @classmethod
    def from_env(cls):
        load_dotenv()
        values = [os.getenv(key, "").strip() for key in ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL")]
        if not all(values):
            raise ValueError("live 模式需要在 .env 中配置 LLM_BASE_URL、LLM_API_KEY、LLM_MODEL")
        return cls(*values)
