"""从环境变量读取模型配置。换模型时改这里对应的变量即可。"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


class ConfigError(RuntimeError):
    """配置缺失或非法。"""


@dataclass(frozen=True)
class Settings:
    api_key: str
    base_url: str
    model: str
    thinking: str
    reasoning_effort: str
    temperature: float
    max_tokens: int
    timeout: float

    @classmethod
    def from_env(cls) -> Settings:
        load_dotenv(override=False)

        api_key = _first("LLM_API_KEY", "DEEPSEEK_API_KEY")
        if not api_key:
            raise ConfigError(
                "未找到 API Key。请在项目目录创建 .env 并设置 LLM_API_KEY，"
                "或在当前环境中导出该变量。格式见 .env.example。"
            )

        thinking = os.getenv("LLM_THINKING", "auto").strip().lower()
        if thinking not in {"auto", "enabled", "disabled"}:
            raise ConfigError("LLM_THINKING 只能是 auto、enabled 或 disabled。")

        effort = os.getenv("LLM_REASONING_EFFORT", "high").strip().lower()
        if effort not in {"low", "high", "max"}:
            raise ConfigError("LLM_REASONING_EFFORT 只能是 low、high 或 max。")

        return cls(
            api_key=api_key,
            base_url=_first("LLM_BASE_URL", "DEEPSEEK_BASE_URL")
            or "https://api.deepseek.com",
            model=os.getenv("LLM_MODEL", "deepseek-v4-pro").strip() or "deepseek-v4-pro",
            thinking=thinking,
            reasoning_effort=effort,
            temperature=_float("LLM_TEMPERATURE", 0.2),
            max_tokens=_int("LLM_MAX_TOKENS", 16384),
            timeout=_float("LLM_TIMEOUT", 180),
        )


def _first(*names: str) -> str:
    for name in names:
        value = os.getenv(name, "").strip()
        if value:
            return value
    return ""


def _float(name: str, default: float) -> float:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} 必须是数字。") from exc


def _int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} 必须是整数。") from exc
    if value <= 0:
        raise ConfigError(f"{name} 必须大于 0。")
    return value
