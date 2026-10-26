"""OpenAI 兼容的聊天模型。DeepSeek 与多数后来可替换的模型都走这一层。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from openai import APIConnectionError, APIStatusError, OpenAI

from linalg_agent.config import Settings


class LinalgAgentError(RuntimeError):
    """调用模型失败。"""


@dataclass
class ModelResponse:
    content: str
    reasoning: str | None
    model: str
    finish_reason: str | None = None
    usage: dict[str, int] | None = None


class ChatModel(Protocol):
    """换成本地模型或非 OpenAI 协议时，实现这个接口再传给 LinalgAgent。"""

    model_name: str

    def complete(self, messages: list[dict[str, str]], *, system: str) -> ModelResponse:
        """发送一次对话并返回正文。"""


@dataclass
class OpenAICompatibleModel:
    api_key: str
    base_url: str
    model: str
    thinking: str = "auto"
    reasoning_effort: str = "high"
    temperature: float = 0.2
    max_tokens: int = 16384
    timeout: float = 180
    client: OpenAI = field(init=False)

    def __post_init__(self) -> None:
        self.base_url = self.base_url.rstrip("/")
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout,
        )

    @classmethod
    def from_settings(cls, settings: Settings) -> OpenAICompatibleModel:
        return cls(
            api_key=settings.api_key,
            base_url=settings.base_url,
            model=settings.model,
            thinking=settings.thinking,
            reasoning_effort=settings.reasoning_effort,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
            timeout=settings.timeout,
        )

    @property
    def model_name(self) -> str:
        return self.model

    @property
    def deepseek_thinking(self) -> bool:
        if self.thinking == "disabled":
            return False
        if self.thinking == "enabled":
            return True
        blob = f"{self.model} {self.base_url}".lower()
        return "deepseek" in blob

    def build_request(self, messages: list[dict[str, str]], *, system: str) -> dict:
        payload: dict = {
            "model": self.model,
            "messages": [{"role": "system", "content": system}, *messages],
            "max_tokens": self.max_tokens,
        }
        if self.deepseek_thinking:
            payload["reasoning_effort"] = self.reasoning_effort
            payload["extra_body"] = {"thinking": {"type": "enabled"}}
        else:
            payload["temperature"] = self.temperature
        return payload

    def complete(self, messages: list[dict[str, str]], *, system: str) -> ModelResponse:
        try:
            response = self.client.chat.completions.create(
                **self.build_request(messages, system=system)
            )
        except APIStatusError as exc:
            detail = exc.message if getattr(exc, "message", None) else str(exc)
            raise LinalgAgentError(f"模型接口返回错误（{exc.status_code}）：{detail}") from exc
        except APIConnectionError as exc:
            raise LinalgAgentError(f"无法连接模型接口：{exc}") from exc

        choice = response.choices[0]
        message = choice.message
        content = (message.content or "").strip()
        if not content:
            raise LinalgAgentError("模型没有返回正文。")
        if choice.finish_reason == "length":
            content += (
                "\n\n（输出因长度上限被截断。可在 .env 中增大 LLM_MAX_TOKENS 后重试。）"
            )

        usage = None
        if response.usage is not None:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens or 0,
                "completion_tokens": response.usage.completion_tokens or 0,
                "total_tokens": response.usage.total_tokens or 0,
            }
        return ModelResponse(
            content=content,
            reasoning=getattr(message, "reasoning_content", None),
            model=response.model or self.model,
            finish_reason=choice.finish_reason,
            usage=usage,
        )
