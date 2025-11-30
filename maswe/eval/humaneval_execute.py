import contextlib
import io
import traceback

SAFE_GLOBALS = {
    "__builtins__": {
        "range": range,
        "len": len,
        "print": print,
        "sum": sum,
        "min": min,
        "max": max,
        "abs": abs,
        "enumerate": enumerate,
        "sorted": sorted,
        "map": map,
        "filter": filter,
        "zip": zip,
        "list": list,
        "dict": dict,
        "set": set,
        "tuple": tuple,
    }
}

def execute_code_with_tests(function_code: str, test_code: str):
    """Executes function_code + test_code in an isolated environment."""
    env = SAFE_GLOBALS.copy()
    buffer = io.StringIO()

    try:
        with contextlib.redirect_stdout(buffer):
            exec(function_code, env)
            exec(test_code, env)
        return True, buffer.getvalue()  # success
    except Exception as e:
        return False, traceback.format_exc()

# ============================================================
# New helpers for HumanEval pipeline
# ============================================================

def check_solution(code: str, entry_point: str, test_code: str):
    """
    兼容 humaneval_pipeline 的接口：
    - code: 模型生成的完整函数代码
    - entry_point: 函数名（目前我们不强制使用它，测试用例会自然调用）
    - test_code: HumanEval 自带的测试代码（assert ...）

    返回:
        {"passed": bool, "error": Optional[str]}
    """
    ok, details = execute_code_with_tests(code, test_code)
    if ok:
        return {"passed": True, "error": None}
    else:
        return {"passed": False, "error": details}


def evaluate_samples(entry_point: str, samples, test_code: str):
    """
    对多次采样的代码进行评测，返回一个 bool 列表：
    [True, False, True, ...]
    """
    results = []
    for code in samples:
        res = check_solution(code, entry_point, test_code)
        results.append(res["passed"])
    return results
