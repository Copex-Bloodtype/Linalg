"""对外的 agent。求解与翻译两条管线共用同一个可替换模型。"""

from __future__ import annotations

from linalg_agent.config import Settings
from linalg_agent.llm import ChatModel, OpenAICompatibleModel
from linalg_agent.method import Method, parse_method
from linalg_agent.pipelines import PipelineResult, SolvePipeline, TranslatePipeline


class LinalgAgent:
    def __init__(self, model: ChatModel) -> None:
        self.model = model
        self.solve_pipeline = SolvePipeline(model)
        self.translate_pipeline = TranslatePipeline(model)

    @classmethod
    def from_env(cls) -> LinalgAgent:
        return cls(OpenAICompatibleModel.from_settings(Settings.from_env()))

    def solve(self, problem: str, *, method: Method | str | None = None) -> PipelineResult:
        """只根据题目作答。

        method 留空时模型自选一种写法。传入 matrix 或 space 时必须使用该写法。
        """
        return self.solve_pipeline.run(problem, method=_coerce(method))

    def alternate(
        self,
        given_solution: str,
        *,
        problem: str | None = None,
        given_method: Method | str | None = None,
    ) -> PipelineResult:
        """把已有的一种解法翻译成另一种，并沿用其中的取法。

        given_method 必须是 matrix 或 space。题目必须单独给出。
        """
        method = _coerce(given_method)
        if method is None:
            raise ValueError("翻译时必须标明已有解法是 matrix 还是 space。")
        return self.translate_pipeline.run(
            given_solution,
            problem=problem or "",
            given_method=method,
        )


def _coerce(value: Method | str | None) -> Method | None:
    if isinstance(value, Method) or value is None:
        return value
    return parse_method(value)
