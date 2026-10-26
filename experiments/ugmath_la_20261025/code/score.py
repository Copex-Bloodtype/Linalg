"""从模型输出的「可核对结论」里抽出填空，并与参照空逐项比较。"""

from __future__ import annotations

import re

import sympy as sp


def extract_blanks(text: str) -> list[str] | None:
    """读取可核对结论里的「结论」行。找不到这一结构时返回 None。"""
    marker = "可核对结论"
    start = text.find(marker)
    window = text[start:] if start >= 0 else text
    match = re.search(r"结论\s*[:：]\s*(.+)", window)
    if match is None:
        return None
    line = match.group(1).strip()
    line = line.splitlines()[0].strip()
    if not line or line in {"无", "见上文"}:
        return None
    parts = [part.strip() for part in line.split("|")]
    parts = [part for part in parts if part]
    return parts or None


def _as_expr(value: str) -> sp.Expr:
    cleaned = value.strip().replace("^", "**")
    cleaned = cleaned.replace("{", "").replace("}", "")
    return sp.simplify(sp.sympify(cleaned))


def blank_equal(got: str, expected: str) -> bool:
    if got.strip() == expected.strip():
        return True
    try:
        return sp.simplify(_as_expr(got) - _as_expr(expected)) == 0
    except (sp.SympifyError, TypeError, ValueError):
        return False


def score_blanks(text: str, expected: list[str]) -> dict:
    got = extract_blanks(text)
    if got is None:
        return {"parsed": False, "correct": None, "n_expected": len(expected), "n_got": 0, "matches": []}
    matches = [blank_equal(left, right) for left, right in zip(got, expected)]
    if len(got) != len(expected):
        matches = []
        correct = False
    else:
        correct = all(matches)
    return {
        "parsed": True,
        "correct": correct,
        "n_expected": len(expected),
        "n_got": len(got),
        "matches": matches,
        "got": got,
    }


def convention_source(text: str) -> str:
    """只看模型有没有写下两种来源用词，不判断它是否真的沿用了取法。"""
    if "继承已有解法" in text:
        return "inherited"
    if "自行选取" in text:
        return "chosen"
    return "unmarked"
