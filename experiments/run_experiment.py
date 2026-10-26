"""跑五种条件，并把每一次请求和原始输出写到实验目录。

已完成且没有错误的记录会跳过，因此中断后可以继续跑。
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import traceback
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from linalg_agent.agent import LinalgAgent
from linalg_agent.config import ConfigError, Settings
from linalg_agent.llm import OpenAICompatibleModel
from linalg_agent.prompts import SOLVE_SYSTEM_PROMPT, TRANSLATE_SYSTEM_PROMPT

from experiments.score import convention_source, score_blanks

EXP = ROOT / "experiments" / "ugmath_la_20261025"
ITEMS = EXP / "sample" / "items.json"
RUNS = EXP / "runs"

BLANK_NOTE = (
    "In the section 可核对结论, the line starting with 结论 must contain only the [ANS] "
    "values in order, separated by ' | '. Do not add words on that line."
)

CONDITIONS = (
    "direct",
    "forced_matrix",
    "forced_space",
    "translate_to_space",
    "translate_to_matrix",
)


class RecordingModel:
    """记下实际送出的提示，避免归档的提示和调用不一致。"""

    def __init__(self, inner: OpenAICompatibleModel) -> None:
        self.inner = inner
        self.model_name = inner.model_name
        self.last_system = ""
        self.last_messages: list[dict[str, str]] = []

    def complete(self, messages, *, system):
        self.last_system = system
        self.last_messages = list(messages)
        return self.inner.complete(messages, system=system)


def main() -> int:
    EXP.mkdir(parents=True, exist_ok=True)
    RUNS.mkdir(parents=True, exist_ok=True)
    _snapshot_code()
    _snapshot_prompts()
    try:
        settings = Settings.from_env()
    except ConfigError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    settings = Settings(
        api_key=settings.api_key,
        base_url=settings.base_url,
        model=settings.model,
        thinking=settings.thinking,
        reasoning_effort=settings.reasoning_effort,
        temperature=settings.temperature,
        max_tokens=settings.max_tokens,
        timeout=max(settings.timeout, 300),
    )
    _write_config(settings)
    payload = json.loads(ITEMS.read_text(encoding="utf-8"))
    recorder = RecordingModel(OpenAICompatibleModel.from_settings(settings))
    agent = LinalgAgent(recorder)
    failures = 0
    for item in payload["items"]:
        for condition in CONDITIONS:
            destination = RUNS / f"{item['id']}__{condition}.json"
            if destination.exists():
                saved = json.loads(destination.read_text(encoding="utf-8"))
                if not saved.get("error"):
                    print(f"skip {item['id']} {condition}", flush=True)
                    continue
            print(f"run {item['id']} {condition}", flush=True)
            record = _run_one(agent, recorder, item, condition)
            destination.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
            if record.get("error"):
                failures += 1
                print(f"error {item['id']} {condition}: {record['error']}", file=sys.stderr, flush=True)
    summary = _summarize(payload)
    (EXP / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    archive = _zip_package()
    print(f"summary {EXP / 'summary.json'}")
    print(f"archive {archive}")
    return 1 if failures else 0


def _run_one(agent: LinalgAgent, recorder: RecordingModel, item: dict, condition: str) -> dict:
    problem = item["problem_v1"].rstrip() + "\n\n" + BLANK_NOTE
    started = _now()
    record = {
        "item_id": item["id"],
        "topic": item["topic"],
        "subtopic": item["subtopic"],
        "condition": condition,
        "version": "v1",
        "problem": item["problem_v1"],
        "dataset_answer": item["answer_v1"],
        "verified_blanks": item["verified_blanks"],
        "reference_conventions": item["conventions"],
        "started_at": started,
    }
    try:
        if condition == "direct":
            result = agent.solve(problem)
        elif condition == "forced_matrix":
            result = agent.solve(problem, method="matrix")
        elif condition == "forced_space":
            result = agent.solve(problem, method="space")
        elif condition == "translate_to_space":
            result = agent.alternate(item["reference_matrix"], problem=problem, given_method="matrix")
        elif condition == "translate_to_matrix":
            result = agent.alternate(item["reference_space"], problem=problem, given_method="space")
        else:
            raise ValueError(f"未知条件：{condition}")
    except Exception as exc:  # 单题失败不应吃掉其余记录
        record["finished_at"] = _now()
        record["error"] = f"{type(exc).__name__}: {exc}"
        record["traceback"] = traceback.format_exc()
        record["request"] = {
            "system": recorder.last_system,
            "messages": recorder.last_messages,
        }
        return record
    record["finished_at"] = _now()
    record["error"] = None
    record["pipeline"] = result.pipeline
    record["result_condition"] = result.condition
    record["model"] = result.model
    record["usage"] = result.usage
    record["reasoning"] = result.reasoning
    record["content"] = result.content
    record["request"] = {"system": recorder.last_system, "messages": recorder.last_messages}
    record["blank_score"] = score_blanks(result.content, item["verified_blanks"])
    record["convention_source"] = convention_source(result.content)
    return record


def _summarize(payload: dict) -> dict:
    by_condition: dict[str, dict] = {}
    calls = []
    for path in sorted(RUNS.glob("*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        calls.append(
            {
                "item_id": record["item_id"],
                "condition": record["condition"],
                "error": record.get("error"),
                "blank_correct": (record.get("blank_score") or {}).get("correct"),
                "convention_source": record.get("convention_source"),
                "usage": record.get("usage"),
            }
        )
        bucket = by_condition.setdefault(
            record["condition"],
            {"calls": 0, "errors": 0, "blank_correct": 0, "blank_scored": 0, "inherited": 0, "chosen": 0},
        )
        bucket["calls"] += 1
        if record.get("error"):
            bucket["errors"] += 1
            continue
        score = record.get("blank_score") or {}
        if score.get("parsed"):
            bucket["blank_scored"] += 1
            if score.get("correct"):
                bucket["blank_correct"] += 1
        source = record.get("convention_source")
        if source == "inherited":
            bucket["inherited"] += 1
        elif source == "chosen":
            bucket["chosen"] += 1
    return {
        "n_items": len(payload["items"]),
        "n_records": len(calls),
        "by_condition": by_condition,
        "calls": calls,
        "scoring_note": "blank_correct 只表示可核对结论里的填空与参照空一致。它不判断写法是否真的换了，也不判断取法是否真的沿用。",
    }


def _snapshot_prompts() -> None:
    prompt_dir = EXP / "prompts"
    prompt_dir.mkdir(parents=True, exist_ok=True)
    (prompt_dir / "solve_system.txt").write_text(SOLVE_SYSTEM_PROMPT, encoding="utf-8")
    (prompt_dir / "translate_system.txt").write_text(TRANSLATE_SYSTEM_PROMPT, encoding="utf-8")
    (prompt_dir / "blank_note.txt").write_text(BLANK_NOTE + "\n", encoding="utf-8")


def _snapshot_code() -> None:
    destination = EXP / "code" / "linalg_agent"
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(
        ROOT / "linalg_agent",
        destination,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    code_dir = EXP / "code"
    for name in ("run_experiment.py", "build_sample.py", "score.py"):
        shutil.copy2(ROOT / "experiments" / name, code_dir / name)


def _write_config(settings: Settings) -> None:
    prompt_hash = {
        "solve_system": hashlib.sha256(SOLVE_SYSTEM_PROMPT.encode("utf-8")).hexdigest(),
        "translate_system": hashlib.sha256(TRANSLATE_SYSTEM_PROMPT.encode("utf-8")).hexdigest(),
    }
    data_hash = (EXP / "data" / "SHA256.txt").read_text(encoding="utf-8").strip()
    config = {
        "dataset": "UGMathBench/ugmathbench",
        "dataset_revision": "8ab16f0c131a9b3b52195e64175cb5a8f3881bbf",
        "subject_file_sha256": data_hash,
        "model": settings.model,
        "base_url": settings.base_url,
        "thinking": settings.thinking,
        "reasoning_effort": settings.reasoning_effort,
        "temperature": settings.temperature,
        "max_tokens": settings.max_tokens,
        "timeout_seconds": settings.timeout,
        "prompt_sha256": prompt_hash,
        "conditions": list(CONDITIONS),
        "api_key_recorded": False,
    }
    (EXP / "config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")


def _zip_package() -> Path:
    archive = EXP.parent / "ugmath_la_20261025.zip"
    if archive.exists():
        archive.unlink()
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as handle:
        for path in EXP.rglob("*"):
            if path.is_file():
                handle.write(path, path.relative_to(EXP.parent))
    return archive


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
