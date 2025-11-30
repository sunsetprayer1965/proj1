import json
from pathlib import Path

DATA_PATH = "/app/maswe/eval/humaneval.jsonl"

def load_humaneval(max_problems=None):
    path = Path(DATA_PATH)
    if not path.exists():
        raise FileNotFoundError(f"HumanEval file not found: {path}")

    dataset = []
    with open(path, "r", encoding="utf8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            dataset.append(obj)
            if max_problems and len(dataset) >= max_problems:
                break

    print(f"[HumanEval] Loaded {len(dataset)} problems.")
    return dataset
