"""把八道路题目和事先写好的两种参照解法冻结成实验样本。

参照解法在任何模型调用之前写定，用来给翻译条件提供输入。
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments" / "ugmath_la_20261025"
RAW = EXP / "sample" / "_raw_items.json"

REFERENCES = {
    "Linear_algebra_0310": {
        "verified_blanks": ["-16", "-9", "20"],
        "conventions": "取 A 的第一列，不取其他列，也不取列的线性组合。",
        "matrix": """Matrix solution.
A is the 3 by 4 matrix with columns c1=(-16,-9,20), c2=(-9,3,6), c3=(20,5,0), c4=(-12,4,8).
The column space is the span of these four columns. Column c1 is not the zero vector, so it belongs to the column space.
Convention locked by this solution: report c1 itself, not another column and not a sum of columns.
Checkable values: -16, -9, 20.
""",
        "space": """Linear-space solution.
Let T: R^4 -> R^3 be T(x)=Ax. The column space of A is the image of T.
The first standard basis vector e1 satisfies T(e1)=Ae1, which is the first column of A. That image is (-16,-9,20), which is not zero, so it is a nonzero vector of im(T).
Convention locked by this solution: use the image of e1, not the image of another basis vector.
Checkable values: -16, -9, 20.
""",
    },
    "Linear_algebra_0494": {
        "verified_blanks": ["-1", "0", "-1", "0", "-1", "-2", "2", "1"],
        "conventions": "核的有序基先写 (-1,0,-1)，再写 (0,-1,-2)；像的基只取 (2,1)。不改用行最简形直接给出的参数基。",
        "matrix": """Matrix solution.
A = [ 2  4  -2 ; 1  2  -1 ].
Row reduction: replace row 2 by row 2 - (1/2) row 1. The second row becomes zero, and row 1 says x + 2y - z = 0, so x = -2y + z.
The general null-space vector is (-2y+z, y, z).
The ordered basis requested here is not the standard parameter basis. Specialize (y,z)=(0,-1) to get (-1,0,-1), then (y,z)=(-1,-2) to get (0,-1,-2).
The single pivot is in column 1, so a basis of the column space is the first column (2,1).
Convention locked by this solution: kernel basis ((-1,0,-1), (0,-1,-2)), image basis ((2,1)).
Checkable values: -1, 0, -1, 0, -1, -2, 2, 1.
""",
        "space": """Linear-space solution.
Let T: R^3 -> R^2, T(x)=Ax. Then ker(T)={x: Ax=0} and im(T)={Ax: x in R^3}.
The equation Ax=0 reduces to the single constraint x = -2y + z. Thus ker(T) is 2-dimensional. Choose the ordered basis
v1=(-1,0,-1), v2=(0,-1,-2).
Both satisfy the constraint, and neither is a scalar multiple of the other, so they form a basis. Do not replace them by (-2,1,0) and (1,0,1).
The two columns of A are parallel: (4,2)=2(2,1) and (-2,-1)=-(2,1). Hence im(T)=span{(2,1)}, and the chosen basis vector of the image is (2,1).
Convention locked by this solution: the same ordered bases as above.
Checkable values: -1, 0, -1, 0, -1, -2, 2, 1.
""",
    },
    "Linear_algebra_0501": {
        "verified_blanks": ["-7", "2", "0", "1", "5", "-2", "1", "0"],
        "conventions": "有序对先写自由变量 x4 对应的向量 u=(-7,2,0,1)，再写自由变量 x3 对应的向量 v=(5,-2,1,0)。",
        "matrix": """Matrix solution.
A = [ 1  3  1  1 ; 0  1  2  -2 ; -1  -2  1  -3 ].
Add row 1 to row 3, then subtract row 2 from the new row 3. Row 3 vanishes.
Back substitution gives x1 = 5 x3 - 7 x4 and x2 = -2 x3 + 2 x4, with x3 and x4 free.
Null-space vector = x3(5,-2,1,0) + x4(-7,2,0,1).
Convention locked by this solution: list the x4-vector first and the x3-vector second,
u=(-7,2,0,1), v=(5,-2,1,0).
Checkable values: -7, 2, 0, 1, 5, -2, 1, 0.
""",
        "space": """Linear-space solution.
Let T: R^4 -> R^3, T(x)=Ax. The set of vectors sent to zero is ker(T).
Solving T(x)=0 produces the plane
ker(T) = span{ (-7,2,0,1), (5,-2,1,0) }.
The first generator is the vector in which the free coordinate x4 equals 1 and x3 equals 0. The second is the vector in which x3 equals 1 and x4 equals 0.
Convention locked by this solution: keep this order. Do not swap the two generators and do not rescale them.
Checkable values: -7, 2, 0, 1, 5, -2, 1, 0.
""",
    },
    "Linear_algebra_0345": {
        "verified_blanks": ["-4", "1", "1", "1", "0", "1", "0", "1", "4", "1", "-1", "0"],
        "answer_note": "数据集 answer_v1 只有 9 个数，对应三个特征向量，缺少三个特征值。核对用 SymPy 复核后的 12 个空。",
        "conventions": "特征值按从小到大 -4, 0, 4。每个特征向量取首个非零坐标为正的那个方向：(1,1,1), (1,0,1), (1,-1,0)。",
        "matrix": """Matrix solution.
A = [ 0  -4  0 ; -8  -4  8 ; -4  -4  4 ].
The characteristic polynomial det(A-λI) has roots λ=-4, λ=0 and λ=4. Order them increasingly: λ1=-4, λ2=0, λ3=4.
For λ=-4, row-reduce A+4I and take the null vector (1,1,1).
For λ=0, row-reduce A and take (1,0,1).
For λ=4, row-reduce A-4I. One null vector is (-1,1,0); multiply by -1 so the first nonzero entry is positive, obtaining (1,-1,0).
Convention locked by this solution: increasing eigenvalues, and the positive-first-entry scaling above.
Checkable values: -4, 1, 1, 1, 0, 1, 0, 1, 4, 1, -1, 0.
""",
        "space": """Linear-space solution.
Let T: R^3 -> R^3, T(x)=Ax. A scalar λ is an eigenvalue when ker(T-λ id) is nontrivial, and its eigenvectors are the nonzero vectors in that kernel.
Those kernels are nontrivial exactly for λ=-4, 0, 4. Order the eigenvalues increasingly.
ker(T+4 id) is spanned by (1,1,1).
ker(T) is spanned by (1,0,1).
ker(T-4 id) is spanned by (1,-1,0), the scalar multiple of (-1,1,0) whose first nonzero coordinate is positive.
Convention locked by this solution: this order and these three generators, not the opposite scaling of the third vector.
Checkable values: -4, 1, 1, 1, 0, 1, 0, 1, 4, 1, -1, 0.
""",
    },
    "Linear_algebra_0313": {
        "verified_blanks": ["-12", "-5", "-19", "-9"],
        "conventions": "B 与 C 都保持题目给出的顺序。P 的第 j 列是 B 的第 j 个向量在 C 下的坐标，不交换两列。",
        "matrix": """Matrix solution.
Let the columns of B be (5,2) and (1,3), and the columns of C be (-2,3) and (1,-2), in the given order.
The change-of-coordinate matrix satisfies P = C^{-1} B.
det(C)=(-2)(-2)-(1)(3)=1, so C^{-1} = [ -2  -1 ; -3  -2 ].
Then P = C^{-1} B = [ -12  -5 ; -19  -9 ].
Convention locked by this solution: do not swap the ordered bases, so the columns stay in this order.
Checkable values: -12, -5, -19, -9.
""",
        "space": """Linear-space solution.
B and C are ordered bases of R^2. The matrix P represents the identity map from (R^2, B) to (R^2, C): its j-th column is the C-coordinate vector of the j-th B-basis vector.
Solve C a = (5,2). Since C^{-1} = [ -2  -1 ; -3  -2 ], the coordinate vector is (-12,-19).
Solve C b = (1,3). The coordinate vector is (-5,-9).
Therefore P = [ -12  -5 ; -19  -9 ].
Convention locked by this solution: column j corresponds to the j-th vector of B in the problem's order.
Checkable values: -12, -5, -19, -9.
""",
    },
    "Linear_algebra_0333": {
        "verified_blanks": ["9+x**2", "x"],
        "conventions": "有序基先写 p(x)=9+x^2，再写 q(x)=x。不交换，也不改用别的标量倍。",
        "matrix": """Matrix solution.
Identify a polynomial a + b x + c x^2 with the coordinate column (a,b,c) in the ordered basis {1, x, x^2}. Degree less than 3 is exactly this 3-dimensional space.
f'(x)=b+2c x, so f'(5)=b+10c and f(1)=a+b+c. The condition f'(5)=f(1) is -a + 9c = 0, or a=9c, with b free.
The coordinate condition is the row (-1, 0, 9). Its null space has the ordered basis (9,0,1), then (0,1,0), corresponding to 9+x^2 and x.
Convention locked by this solution: p(x)=9+x^2 and q(x)=x, in that order.
Checkable values: 9+x^2, x.
""",
        "space": """Linear-space solution.
Let V={f in P_3[x]: f'(5)=f(1)}, where P_3[x] means polynomials of degree less than 3. A general element is f(x)=a+bx+cx^2.
The condition f'(5)=f(1) is one linear constraint and forces a=9c, while b stays free. Hence every such f is
f(x)=c(9+x^2)+b x,
so {9+x^2, x} spans V. The two polynomials are linearly independent, and dim V=2, so they form a basis.
Convention locked by this solution: name p(x)=9+x^2 and q(x)=x. Do not swap them.
Checkable values: 9+x^2, x.
""",
    },
    "Linear_algebra_0054": {
        "verified_blanks": [
            "-39-4*x2+4*x3+3*x4",
            "x2",
            "x3",
            "x4",
            "57+x7",
            "-19+x7",
            "x7",
            "-6",
        ],
        "answer_note": "数据集给出未化简的回代表达式。SymPy 化简后与上面八个式子相同。自由变量仍是 x2, x3, x4, x7。",
        "conventions": "自由变量按列号取 x2、x3、x4、x7。特解取这些自由变量全为 0 的那一个：(-39,0,0,0,57,-19,0,-6)。",
        "matrix": """Matrix solution.
The augmented matrix is already in echelon form, with pivots in columns 1, 5, 6 and 8.
Back-substitution yields
x8 = -6,
x6 = x7 - 19,
x5 = x7 + 57,
x1 = -39 - 4 x2 + 4 x3 + 3 x4,
while x2, x3, x4 and x7 are free.
Convention locked by this solution: keep exactly these free variables. The particular solution is the one in which every free variable is 0, namely (-39,0,0,0,57,-19,0,-6). Do not move the particular solution by adding a null-space vector.
Checkable values, in order x1 through x8: -39-4*x2+4*x3+3*x4, x2, x3, x4, 57+x7, -19+x7, x7, -6.
""",
        "space": """Linear-space solution.
Let the coefficient matrix be the 4 by 8 matrix of the given system, and let T(x)=Ax on R^8. The solution set is one particular solution plus ker(T).
Read the pivots: free coordinates are x2, x3, x4, x7, in that index order. Set all of them to 0 to choose the particular solution
p = (-39, 0, 0, 0, 57, -19, 0, -6).
The corresponding ordered basis of the kernel is
(-4,1,0,0,0,0,0,0), (4,0,1,0,0,0,0,0), (3,0,0,1,0,0,0,0), (0,0,0,0,1,1,1,0).
Convention locked by this solution: this particular solution and this order of free variables.
Checkable values, in order x1 through x8: -39-4*x2+4*x3+3*x4, x2, x3, x4, 57+x7, -19+x7, x7, -6.
""",
    },
    "Linear_algebra_0468": {
        "verified_blanks": ["1", "6", "36", "0", "8", "96", "0", "0", "64"],
        "conventions": "定义域和到达域都使用题目给出的有序基 {1, t, t^2}。第 j 列是 T 作用在第 j 个基向量上的坐标，不按行填写。",
        "matrix": """Matrix solution.
Use the ordered basis {1, t, t^2}. Compute the images and expand them in this basis.
T(1)=1, with coordinates (1,0,0).
T(t)=8t+6, with coordinates (6,8,0).
T(t^2)=(8t+6)^2=36+96t+64t^2, with coordinates (36,96,64).
Place these coordinates in the columns:
A = [ 1  6  36 ; 0  8  96 ; 0  0  64 ].
Convention locked by this solution: column j is the coordinate vector of T applied to the j-th basis polynomial. Do not transpose the matrix.
Checkable values, row by row: 1, 6, 36, 0, 8, 96, 0, 0, 64.
""",
        "space": """Linear-space solution.
T: P_2 -> P_2 is the linear map T(f)(t)=f(8t+6). Relative to the ordered basis B={1, t, t^2} of both domain and codomain, the matrix of T is defined by using [T(b_j)]_B as its j-th column.
T(1)=1 gives column (1,0,0).
T(t)=6+8t gives column (6,8,0).
T(t^2)=36+96t+64t^2 gives column (36,96,64).
So [T]_B = [ 1  6  36 ; 0  8  96 ; 0  0  64 ].
Convention locked by this solution: the basis order is the one in the problem, and the matrix is filled by columns.
Checkable values, row by row: 1, 6, 36, 0, 8, 96, 0, 0, 64.
""",
    },
}


def main() -> None:
    raw_items = json.loads(RAW.read_text(encoding="utf-8"))
    items = []
    for raw in raw_items:
        ref = REFERENCES[raw["id"]]
        blanks = raw["problem_v1"].count("[ANS]")
        if len(ref["verified_blanks"]) != blanks:
            raise SystemExit(f"{raw['id']} 有 {blanks} 个空，参照答案有 {len(ref['verified_blanks'])} 个。")
        items.append(
            {
                **raw,
                "version": "v1",
                "verified_blanks": ref["verified_blanks"],
                "conventions": ref["conventions"],
                "answer_note": ref.get("answer_note", ""),
                "reference_matrix": ref["matrix"].strip() + "\n",
                "reference_space": ref["space"].strip() + "\n",
            }
        )
    payload = {
        "authored_before_model_calls": True,
        "version_used": "v1",
        "selection": [
            "从五种同时容许矩阵计算和线性空间叙述的主题中各取一道，而不是随机抽到纯抄写或迭代法的题。",
            "Linear_algebra_0310：列空间里的一个非零向量，取哪一列是不唯一的。",
            "Linear_algebra_0494：核与像的基，顺序和缩放不唯一。",
            "Linear_algebra_0501：核的一对生成元，顺序不唯一。",
            "Linear_algebra_0345：特征值按题目要求从小到大，特征向量的缩放不唯一。",
            "Linear_algebra_0313：过渡矩阵由有序基决定，列与基向量的对应是两种写法的关联。",
            "Linear_algebra_0333：多项式空间的有序基不唯一。",
            "Linear_algebra_0054：自由变量和特解的取法不唯一。",
            "Linear_algebra_0468：线性映射在指定有序基下的矩阵，列与 T(基向量) 的对应是关联本身。",
            "未收入只要求抄增广矩阵、只问定义域维数、Gauss-Seidel 迭代，或题干已经给出行最简形的题。",
        ],
        "items": items,
    }
    out = EXP / "sample" / "items.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {out} ({len(items)} items)")


if __name__ == "__main__":
    main()
