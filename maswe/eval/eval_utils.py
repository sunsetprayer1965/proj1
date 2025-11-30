import re

def clean_completion_text(text):
    """Remove markdown, ```python, stray text, explanations."""
    text = text.strip()
    text = text.replace("```python", "").replace("```", "")
    return text.strip()


def extract_function(text):
    """
    Extract the first python function definition
    """
    pattern = r"def\s+\w+\(.*?\):([\s\S]+)"
    m = re.search(pattern, text)
    if m:
        return "def " + text.split("def ", 1)[1]
    return text  # fallback

def compute_pass_at_k(n: int, c: int, k: int) -> float:
    """
    Standard pass@k metric from HumanEval paper:
        pass@k = 1 - comb(n - c, k) / comb(n, k)
    Where:
        n = total samples
        c = correct samples
        k = number of tries (e.g. 1, 3, 5)

    If n < k:
        return 1.0 if c > 0 else 0.0
    """
    import math

    if c == 0:
        return 0.0
    if n < k:
        return float(c > 0)

    return 1 - (math.comb(n - c, k) / math.comb(n, k))