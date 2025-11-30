#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import asyncio
import os
from datetime import datetime
import json
import re

from metagpt.configs.llm_config import LLMConfig
from metagpt.llm import LLM

# HumanEval pipeline
from maswe.eval.humaneval_pipeline import (
    load_humaneval,
    evaluate_humaneval_solutions,
)

# Optional: logging adapter (if you enable --log-agent)
try:
    from maswe.eval.agent_logger import AgentLogger
except Exception:
    AgentLogger = None


# ============================================================
# Utility
# ============================================================

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)
    return path


def extract_code(text: str) -> str:
    """
 
    """
    if not isinstance(text, str):
        return ""

 
    code_blocks = re.findall(r"```(?:python)?\s*(.*?)```", text, flags=re.S | re.I)
    if code_blocks:
        return code_blocks[0].strip()


    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.lstrip().startswith("def ") or line.lstrip().startswith("class "):
            return "\n".join(lines[i:]).strip()


    return text.strip()


# ============================================================
# HumanEval Runner
# ============================================================

async def run_humaneval(args):
    print("\n🧪 STARTING HumanEval evaluation")
    print(f"   Model       : {args.model}")
    print(f"   n_samples   : {args.n_samples}")
    print("============================================================")

    # Load dataset
    dataset = load_humaneval(max_problems=args.max_problems)
    print(f"[HumanEval] Loaded {len(dataset)} problems.\n")

    # Setup logging directory
    log_dir = None
    if args.log_agent:
        run_id = args.run_id or datetime.now().strftime("%Y%m%d-%H%M%S")
        log_dir = ensure_dir(f"/workspace/agent_logs/{run_id}")

        if AgentLogger:
            AgentLogger.init_global(log_dir)
            print(f"📁 Agent logs enabled → {log_dir}")

    # Configure LLM → 强制使用 Ollama
    from metagpt.configs.llm_config import LLMType

    llm_config = LLMConfig(
        api_type=LLMType.OLLAMA,                      # 使用 Ollama provider
        model=args.model,
        base_url="http://host.docker.internal:11434", # 
        api_key="EMPTY",                              
        temperature=0.0,
        max_tokens=2048,
    )
    llm = LLM(llm_config=llm_config)
    print(f"[DEBUG] api_type  = {llm_config.api_type}")
    print(f"[DEBUG] model     = {llm_config.model}")
    print(f"[DEBUG] base_url  = {llm_config.base_url}")

    # Generate solutions
    all_results = []

    print(" Loaded HumanEval problems")
    print(" Starting HumanEval generation...\n")

    for ex in dataset:
        print("=" * 28)
        print(f" Problem {ex['task_id']}")
        print("=" * 28)

        # 对当前这个 task 采样多次，收集纯代码字符串
        code_samples = []

        for i in range(args.n_samples):
            prompt = ex["prompt"]

            # LLM call
            resp = await llm.aask(prompt)
            code_raw = resp if isinstance(resp, str) else getattr(resp, "text", str(resp))

            # 只保留真正的 Python 代码
            code_clean = extract_code(code_raw)
            code_samples.append(code_clean)

            # Optional logging：把原始输出也一起记下来
            if log_dir:
                with open(os.path.join(log_dir, "llm_calls.jsonl"), "a", encoding="utf8") as f:
                    f.write(json.dumps({
                        "task_id": ex["task_id"],
                        "sample_id": i,
                        "prompt": prompt,
                        "response_raw": code_raw,
                        "response_code": code_clean,
                    }) + "\n")

        # 按 humaneval_pipeline 的接口格式包装
        formatted = [{
            "task_id": ex["task_id"],
            "entry_point": ex["entry_point"],
            "samples": code_samples,  # 只传纯代码字符串进去
            "test": ex["test"],
        }]

        # Evaluate
        summary = evaluate_humaneval_solutions(formatted, k=args.n_samples)
        pass_list = summary[0]["results"]
        score = summary[0]["pass@k"]

        print(f"  pass@{args.n_samples}: {score:.2f}")
        print(f"  sample results: {pass_list}\n")

        all_results.append(score)

    print("========================================")
    if all_results:
        print(f"  Final pass@{args.n_samples}: {sum(all_results)/len(all_results):.3f}")
    else:
        print(" Final pass: N/A (no problems evaluated)")
    print("========================================")


# ============================================================
# Argument Parser
# ============================================================

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--eval-humaneval", action="store_true")
    parser.add_argument("--model", type=str, default="qwen2.5-coder:7b")
    parser.add_argument("--n-samples", type=int, default=1)
    parser.add_argument("--max-problems", type=int, default=None)

    # Logging
    parser.add_argument("--log-agent", action="store_true")
    parser.add_argument("--run-id", type=str, default=None)

    return parser.parse_args()


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    args = parse_args()

    if args.eval_humaneval:
        asyncio.run(run_humaneval(args))
    else:
        print(" SWE multi-agent mode is not supported in this MetaGPT version.")
        print("   Only:  --eval-humaneval  is available.")
