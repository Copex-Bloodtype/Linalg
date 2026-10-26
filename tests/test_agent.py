import os
import unittest
from unittest.mock import patch

from linalg_agent.agent import LinalgAgent
from linalg_agent.cli import main
from linalg_agent.config import ConfigError, Settings
from linalg_agent.llm import ModelResponse, OpenAICompatibleModel
from linalg_agent.method import Method, parse_method
from linalg_agent.prompts import SOLVE_SYSTEM_PROMPT, TRANSLATE_SYSTEM_PROMPT


class FakeModel:
    model_name = "fake"

    def __init__(self) -> None:
        self.calls: list[tuple[str, list[dict[str, str]]]] = []

    def complete(self, messages, *, system):
        self.calls.append((system, messages))
        return ModelResponse(content="解答", reasoning="思考", model=self.model_name)


class PipelineTests(unittest.TestCase):
    def test_solve_sends_problem_to_direct_prompt(self) -> None:
        model = FakeModel()
        result = LinalgAgent(model).solve("  求 A 的秩  ")
        self.assertEqual(result.pipeline, "solve")
        self.assertEqual(result.condition, "direct")
        self.assertEqual(result.meta["requested_method"], "free")
        self.assertEqual(result.content, "解答")
        system, messages = model.calls[0]
        self.assertIs(system, SOLVE_SYSTEM_PROMPT)
        self.assertIn("求 A 的秩", messages[0]["content"])
        self.assertIn("只自选", messages[0]["content"])

    def test_forced_methods_are_separate_conditions(self) -> None:
        matrix_model = FakeModel()
        matrix = LinalgAgent(matrix_model).solve("求通解", method="matrix")
        self.assertEqual(matrix.condition, "forced_matrix")
        self.assertIn("必须使用矩阵解法", matrix_model.calls[0][1][0]["content"])
        self.assertNotIn("已有解法", matrix_model.calls[0][1][0]["content"])

        space_model = FakeModel()
        space = LinalgAgent(space_model).solve("求通解", method=Method.LINEAR_SPACE)
        self.assertEqual(space.condition, "forced_space")
        self.assertIn("必须使用线性空间解法", space_model.calls[0][1][0]["content"])

    def test_solve_rejects_blank_problem(self) -> None:
        with self.assertRaises(ValueError):
            LinalgAgent(FakeModel()).solve("   ")

    def test_matrix_solution_asks_for_linear_space(self) -> None:
        model = FakeModel()
        result = LinalgAgent(model).alternate(
            "对增广矩阵做初等行变换。",
            problem="解方程组",
            given_method="matrix",
        )
        self.assertEqual(result.pipeline, "translate")
        self.assertEqual(result.condition, "translate_to_space")
        self.assertEqual(result.meta["given_method"], "matrix")
        self.assertEqual(result.meta["target_method"], "linear_space")
        system, messages = model.calls[0]
        self.assertIs(system, TRANSLATE_SYSTEM_PROMPT)
        text = messages[0]["content"]
        self.assertIn("矩阵解法", text)
        self.assertIn("线性空间解法", text)
        self.assertIn("解方程组", text)
        self.assertIn("初等行变换", text)
        self.assertIn("不要改成你自己更习惯的取法", text)

    def test_space_solution_asks_for_matrix(self) -> None:
        model = FakeModel()
        result = LinalgAgent(model).alternate(
            "解空间由核的一组基张成。",
            problem="求通解",
            given_method=Method.LINEAR_SPACE,
        )
        self.assertEqual(result.condition, "translate_to_matrix")
        text = model.calls[0][1][0]["content"]
        self.assertIn("必须给出", text)
        self.assertIn("矩阵解法", text)

    def test_translate_requires_problem_and_method(self) -> None:
        agent = LinalgAgent(FakeModel())
        with self.assertRaises(ValueError):
            agent.alternate("一份解法。", problem="题目")
        with self.assertRaises(ValueError):
            agent.alternate("一份解法。", given_method="matrix")

    def test_alternate_rejects_blank_solution(self) -> None:
        with self.assertRaises(ValueError):
            LinalgAgent(FakeModel()).alternate("  ", problem="题目", given_method="matrix")


class MethodTests(unittest.TestCase):
    def test_aliases(self) -> None:
        self.assertIs(parse_method("矩阵"), Method.MATRIX)
        self.assertIs(parse_method("space"), Method.LINEAR_SPACE)
        self.assertIsNone(parse_method("auto"))
        self.assertIsNone(parse_method(None))

    def test_other(self) -> None:
        self.assertIs(Method.MATRIX.other, Method.LINEAR_SPACE)
        self.assertIs(Method.LINEAR_SPACE.other, Method.MATRIX)


class SettingsTests(unittest.TestCase):
    def test_missing_key(self) -> None:
        with patch("linalg_agent.config.load_dotenv"):
            with patch.dict(os.environ, {}, clear=True):
                with self.assertRaises(ConfigError):
                    Settings.from_env()

    def test_generic_key_overrides_deepseek_name(self) -> None:
        env = {
            "LLM_API_KEY": "generic",
            "DEEPSEEK_API_KEY": "deepseek",
            "LLM_MODEL": "other-model",
            "LLM_BASE_URL": "https://example.test/v1",
            "LLM_THINKING": "disabled",
        }
        with patch("linalg_agent.config.load_dotenv"):
            with patch.dict(os.environ, env, clear=True):
                settings = Settings.from_env()
        self.assertEqual(settings.api_key, "generic")
        self.assertEqual(settings.model, "other-model")
        self.assertEqual(settings.base_url, "https://example.test/v1")
        self.assertEqual(settings.thinking, "disabled")


class CliTests(unittest.TestCase):
    def test_solve_command_uses_direct_pipeline(self) -> None:
        model = FakeModel()
        with patch("linalg_agent.cli.LinalgAgent.from_env", return_value=LinalgAgent(model)):
            code = main(["solve", "求秩"])
        self.assertEqual(code, 0)
        self.assertIs(model.calls[0][0], SOLVE_SYSTEM_PROMPT)
        self.assertIn("求秩", model.calls[0][1][0]["content"])

    def test_solve_command_can_force_matrix(self) -> None:
        model = FakeModel()
        with patch("linalg_agent.cli.LinalgAgent.from_env", return_value=LinalgAgent(model)):
            code = main(["solve", "--method", "matrix", "求秩"])
        self.assertEqual(code, 0)
        self.assertIn("必须使用矩阵解法", model.calls[0][1][0]["content"])

    def test_alternate_command_maps_space_to_matrix(self) -> None:
        model = FakeModel()
        with patch("linalg_agent.cli.LinalgAgent.from_env", return_value=LinalgAgent(model)):
            code = main(
                ["alternate", "--given", "space", "-p", "题目", "-s", "用基和维数说明"]
            )
        self.assertEqual(code, 0)
        self.assertIn("矩阵解法", model.calls[0][1][0]["content"])
        self.assertIn("不要改成你自己更习惯的取法", model.calls[0][1][0]["content"])

    def test_alternate_requires_given_and_problem(self) -> None:
        with self.assertRaises(SystemExit) as caught:
            main(["alternate", "-s", "一份解法"])
        self.assertEqual(caught.exception.code, 2)
        self.assertEqual(main(["alternate", "--given", "matrix", "-s", "一份解法"]), 1)

    def test_missing_problem_exits_with_error(self) -> None:
        self.assertEqual(main(["solve"]), 1)


class RequestTests(unittest.TestCase):
    def test_deepseek_enables_thinking_by_default(self) -> None:
        model = OpenAICompatibleModel(
            api_key="test",
            base_url="https://api.deepseek.com",
            model="deepseek-v4-pro",
        )
        payload = model.build_request([{"role": "user", "content": "hi"}], system="sys")
        self.assertEqual(payload["model"], "deepseek-v4-pro")
        self.assertEqual(payload["extra_body"], {"thinking": {"type": "enabled"}})
        self.assertEqual(payload["reasoning_effort"], "high")
        self.assertNotIn("temperature", payload)
        self.assertEqual(payload["messages"][0]["content"], "sys")

    def test_other_provider_omits_deepseek_extras(self) -> None:
        model = OpenAICompatibleModel(
            api_key="test",
            base_url="https://example.test/v1",
            model="some-other-model",
            temperature=0.2,
        )
        payload = model.build_request([{"role": "user", "content": "hi"}], system="sys")
        self.assertNotIn("extra_body", payload)
        self.assertNotIn("reasoning_effort", payload)
        self.assertEqual(payload["temperature"], 0.2)

    def test_explicit_thinking_can_be_forced_on(self) -> None:
        model = OpenAICompatibleModel(
            api_key="test",
            base_url="https://example.test/v1",
            model="some-other-model",
            thinking="enabled",
        )
        payload = model.build_request([{"role": "user", "content": "hi"}], system="sys")
        self.assertIn("extra_body", payload)


if __name__ == "__main__":
    unittest.main()
