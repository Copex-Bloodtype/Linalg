# 线性代数解题 agent

所有管线，共用一个可替换的模型。当前默认是 DeepSeek V4 Pro（`deepseek-v4-pro`）。同一道题可以跑五种条件，用来比较模型是会做题，还是真的能在两种写法之间翻译。

求解管线只看题目：

1. **直接求解**：模型自选矩阵解法或线性空间解法中的一种。
2. **指定矩阵解法**。
3. **指定线性空间解法**。

翻译管线看题目和其中一种解法，写成另一种，并沿用原解法里的自由变量、特解、基的顺序与缩放等取法：

4. **矩阵解法翻译成线性空间解法**。
5. **线性空间解法翻译成矩阵解法**。

两种管线都要求写出约定、约定来源和一份可核对结论。提示词让翻译写「继承已有解法」，让求解写「自行选取」。这个标签只说明模型写了哪个词，不说明取法真的被沿用，也不说明写法真的换了。

## 安装

需要 Python 3.9 或更高。这台机器上的 `python` 是应用商店占位程序，用 `py -3.9`：

```powershell
cd C:\Users\CopexAV\Desktop\linalg
py -3.9 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
copy .env.example .env
```

编辑 `.env`，填入 `LLM_API_KEY`。不调用模型的检查：

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_agent
```

## 使用

直接求解，或指定写法：

```powershell
linalg-agent solve -f examples\problem.txt
linalg-agent solve --method matrix "求矩阵 [[1,2],[3,4]] 的逆"
linalg-agent solve --method space -f examples\problem.txt
```

把一份矩阵解法翻译成线性空间解法。`--given` 和题目都要给：

```powershell
linalg-agent alternate --given matrix -f examples\matrix_solution.txt -p "在实数域上求该方程组的通解"
```

反向翻译：

```powershell
linalg-agent alternate --given space --problem-file examples\problem.txt -s "已有的线性空间解法"
```

`--reasoning` 会在答案后附上思考过程，`--usage` 会在标准错误里打印 token 用量。

## 在代码里调用

```python
from linalg_agent import LinalgAgent

agent = LinalgAgent.from_env()
print(agent.solve("求这个方程组的通解：...").condition)
print(agent.solve("同一道题", method="matrix").content)
print(agent.solve("同一道题", method="space").content)
print(agent.alternate("（一份矩阵解法）", problem="同一道题", given_method="matrix").content)
```

## 换模型

接口是 OpenAI Chat Completions 兼容时，只改 `.env`：

```env
LLM_API_KEY=新的密钥
LLM_BASE_URL=https://新的地址/v1
LLM_MODEL=新的模型名
LLM_THINKING=auto
```

`LLM_THINKING=auto` 时，只有地址或模型名里含 `deepseek` 才会附带思考模式参数。新厂商不支持这些参数时保持 `auto` 即可；要强制打开或关闭，设成 `enabled` 或 `disabled`。

如果新模型不是这套协议，实现 `ChatModel`（一个 `complete(messages, system=...)` 方法），再 `LinalgAgent(your_model)`。两条管线不用改。

## 试点

2026-10-25 从 UGMathBench 线性代数里固定了 8 道题，五种条件各调用一次，共 40 次。记录在 `experiments/ugmath_la_20261025/`，调用前的方案在该目录的 `PROTOCOL.md`。压缩包 `experiments/ugmath_la_20261025.zip` 是当时的归档。这个目录不再改。

`summary.json` 里的填空对错只表示「可核对结论」那一行和参照空一致。它不判断结论在模型自己的取法下是否成立，也不判断写法有没有换。

人工三项分在 `experiments/pilot_rubric/`：

- `RUBRIC.md`：结论、取法、写法怎么判
- `scores.json`：40 份的分数。要改分，改这个文件

按这三项，0310 的翻译是取法相同但结论错；特征值题的空间写法是结论对但只换了名字；方程组、多项式基和核空间的翻译是取法相同并且写法换了。样本只有这 8 道，不能当成模型已经理解两种解法关联的比例。
