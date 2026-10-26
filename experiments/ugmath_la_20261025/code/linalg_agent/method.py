"""矩阵解法与线性空间解法。"""

from __future__ import annotations

from enum import Enum


class Method(str, Enum):
    MATRIX = "matrix"
    LINEAR_SPACE = "linear_space"

    @property
    def label(self) -> str:
        if self is Method.MATRIX:
            return "矩阵解法"
        return "线性空间解法"

    @property
    def other(self) -> Method:
        if self is Method.MATRIX:
            return Method.LINEAR_SPACE
        return Method.MATRIX


_ALIASES = {
    "matrix": Method.MATRIX,
    "矩阵": Method.MATRIX,
    "矩阵解法": Method.MATRIX,
    "space": Method.LINEAR_SPACE,
    "linear_space": Method.LINEAR_SPACE,
    "linear-space": Method.LINEAR_SPACE,
    "线性空间": Method.LINEAR_SPACE,
    "线性空间解法": Method.LINEAR_SPACE,
}


def parse_method(value: str | None) -> Method | None:
    """把用户写的方法名解析成 Method。auto / 空 表示交给模型判断。"""
    if value is None:
        return None
    text = value.strip()
    if text.lower() in {"", "auto", "自动", "free", "自由"}:
        return None
    key = text.lower()
    if key in _ALIASES:
        return _ALIASES[key]
    if text in _ALIASES:
        return _ALIASES[text]
    accepted = "free、matrix、space"
    raise ValueError(f"无法识别的解法类型：{value}。可用值为 {accepted}。")
