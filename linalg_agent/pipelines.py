"""求解管线与翻译管线。五种条件是这两条管线的参数，不是五套提示。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from linalg_agent.llm import ChatModel, ModelResponse
from linalg_agent.method import Method
from linalg_agent.prompts import (
    SOLVE_SYSTEM_PROMPT,
    TRANSLATE_SYSTEM_PROMPT,
    render_solve_user,
    render_translate_user,
)


class Condition(str, Enum):
    """同一道题上的五种实验条件。"""

    DIRECT = "direct"
    FORCED_MATRIX = "forced_matrix"
    FORCED_SPACE = "forced_space"
    TRANSLATE_TO_MATRIX = "translate_to_matrix"
    TRANSLATE_TO_SPACE = "translate_to_space"

    @classmethod
    def for_solve(cls, method: Method | None) -> Condition:
        if method is None:
            return cls.DIRECT
        if method is Method.MATRIX:
            return cls.FORCED_MATRIX
        return cls.FORCED_SPACE

    @classmethod
    def for_translate(cls, given_method: Method) -> Condition:
        if given_method is Method.MATRIX:
            return cls.TRANSLATE_TO_SPACE
        return cls.TRANSLATE_TO_MATRIX


@dataclass
class PipelineResult:
    pipeline: str
    condition: str
    content: str
    reasoning: str | None
    model: str
    meta: dict[str, str] = field(default_factory=dict)
    usage: dict[str, int] | None = None

    @classmethod
    def from_response(
        cls,
        pipeline: str,
        condition: Condition,
        response: ModelResponse,
        meta: dict[str, str] | None = None,
    ) -> PipelineResult:
        merged = {"condition": condition.value}
        if meta:
            merged.update(meta)
        return cls(
            pipeline=pipeline,
            condition=condition.value,
            content=response.content,
            reasoning=response.reasoning,
            model=response.model,
            meta=merged,
            usage=response.usage,
        )


class SolvePipeline:
    """只看题目。写法可以自由选择，也可以指定矩阵解法或线性空间解法。"""

    name = "solve"

    def __init__(self, model: ChatModel) -> None:
        self.model = model

    def run(self, problem: str, *, method: Method | None = None) -> PipelineResult:
        problem = problem.strip()
        if not problem:
            raise ValueError("题目不能为空。")
        condition = Condition.for_solve(method)
        response = self.model.complete(
            [{"role": "user", "content": render_solve_user(problem, method)}],
            system=SOLVE_SYSTEM_PROMPT,
        )
        return PipelineResult.from_response(
            self.name,
            condition,
            response,
            meta={
                "requested_method": method.value if method else "free",
                "given_method": "",
                "target_method": method.value if method else "free",
            },
        )


class TranslatePipeline:
    """看同一道题和其中一种解法，写成另一种，并沿用原解法里的取法。"""

    name = "translate"

    def __init__(self, model: ChatModel) -> None:
        self.model = model

    def run(
        self,
        given_solution: str,
        *,
        problem: str,
        given_method: Method,
    ) -> PipelineResult:
        given_solution = given_solution.strip()
        problem = problem.strip()
        if not problem:
            raise ValueError("翻译时必须提供题目，这样才和求解管线看的是同一道题。")
        if not given_solution:
            raise ValueError("已有解法不能为空。")
        if not isinstance(given_method, Method):
            raise ValueError("翻译时必须标明已有解法是 matrix 还是 space。")
        condition = Condition.for_translate(given_method)
        response = self.model.complete(
            [
                {
                    "role": "user",
                    "content": render_translate_user(problem, given_solution, given_method),
                }
            ],
            system=TRANSLATE_SYSTEM_PROMPT,
        )
        return PipelineResult.from_response(
            self.name,
            condition,
            response,
            meta={
                "requested_method": given_method.other.value,
                "given_method": given_method.value,
                "target_method": given_method.other.value,
            },
        )
