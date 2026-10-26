# UGMathBench 线性代数五种条件

模型调用开始之前写定。密钥不进入本目录。

## 问题

同一批题目上，模型是会做题，还是能在矩阵解法和线性空间解法之间翻译，并沿用原解法里的取法。

## 数据

- 数据集：UGMathBench/ugmathbench，修订 `8ab16f0c131a9b3b52195e64175cb5a8f3881bbf`
- 文件：`data/Linear_algebra.json`，SHA256 见 `data/SHA256.txt`
- 只用 `problem_v1` 与 `answer_v1`
- 全科 498 题里先限定到方程组、欧氏空间、线性变换、特征值、抽象向量空间中两种写法都说得通的子题，再固定下面 8 道。不在看到模型输出之后更换。

| 编号 | 要锁住的取法 |
| --- | --- |
| Linear_algebra_0310 | 列空间里取第一列 |
| Linear_algebra_0494 | 核与像的有序基 |
| Linear_algebra_0501 | 核的两个生成元的顺序 |
| Linear_algebra_0345 | 特征值从小到大，特征向量取首个非零坐标为正 |
| Linear_algebra_0313 | 有序基决定过渡矩阵的列 |
| Linear_algebra_0333 | 有序基先 `9+x^2` 再 `x` |
| Linear_algebra_0054 | 自由变量 `x2,x3,x4,x7`，特解取自由变量为 0 |
| Linear_algebra_0468 | 矩阵按列填写，基顺序为 `{1,t,t^2}` |

`Linear_algebra_0345` 的数据集答案只有 9 个数，缺了三个特征值。填空对错按 SymPy 复核后的 12 个空计，原始答案仍保存在每条记录的 `dataset_answer`。

## 五种条件

每道题按这个顺序各跑一次：

1. `direct`：只给题目，模型自选一种写法
2. `forced_matrix`：只给题目，必须用矩阵解法
3. `forced_space`：只给题目，必须用线性空间解法
4. `translate_to_space`：题目加事先写好的矩阵参照解法
5. `translate_to_matrix`：题目加事先写好的线性空间参照解法

参照解法在 `sample/items.json`，字段 `authored_before_model_calls` 为真。翻译条件使用这份参照，不用同一次实验里模型自己的求解输出。

## 记录

每次调用写成 `runs/<题号>__<条件>.json`，里面有实际送出的系统提示和用户提示、正文、思考过程、token 用量和错误。没有错误的记录会在重跑时跳过。

`summary.json` 里的填空是否正确，只表示「可核对结论」那一行与参照空一致。它不判断写法有没有换，也不判断取法有没有真的沿用。`convention_source` 只记录模型有没有写下「继承已有解法」或「自行选取」。

## 模型

读取项目 `.env` 的 `LLM_MODEL`、`LLM_BASE_URL`、`LLM_THINKING`、`LLM_REASONING_EFFORT`、`LLM_MAX_TOKENS`。单次等待至少 300 秒。密钥不写入 `config.json`。
