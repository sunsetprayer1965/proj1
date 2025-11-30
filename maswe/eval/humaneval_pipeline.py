import json
import asyncio
from typing import List, Dict, Any
from maswe.eval.humaneval_execute import check_solution, evaluate_samples
from maswe.eval.eval_utils import compute_pass_at_k
def load_humaneval(max_problems=None):
    return load_humaneval_dataset(max_problems=max_problems)

# ================================================================
# Load dataset
# ================================================================
def load_humaneval_dataset(path="maswe/eval/humaneval.jsonl", max_problems=None):
    dataset = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            dataset.append(obj)
            if max_problems and len(dataset) >= max_problems:
                break
    return dataset


# ================================================================
# Generate multiple samples for one problem
# ================================================================
async def generate_code_samples(model, prompt: str, n_samples: int):
    samples = []
    for _ in range(n_samples):
        out = await model.run(prompt)
        samples.append(out)
    return samples


# ================================================================
# Evaluate pass@k for one HumanEval problem
# ================================================================
def evaluate_problem_passk(entry_point: str, samples: List[str], test_code: str, k=3):
    results = evaluate_samples(entry_point, samples, test_code)
    num_correct = sum(results)
    num_total = len(results)
    pass_k = compute_pass_at_k(num_total, num_correct, k)
    return {
        "num_correct": num_correct,
        "num_total": num_total,
        "results": results,
        "pass@k": pass_k,
    }


# ================================================================
# Single agent wrapper for HumanEval
# ================================================================
def build_single_agent_runner(llm):
    async def runner(problem):
        prompt = problem["prompt"]
        entry_point = problem["entry_point"]
        test_code = problem["test"]
        n_samples = problem.get("n_samples", 1)

        samples = await generate_code_samples(llm, prompt, n_samples)
        result = evaluate_problem_passk(entry_point, samples, test_code, k=n_samples)
        result["samples"] = samples
        return result

    return runner


# ================================================================
# Required export: generate_humaneval_solutions
# ================================================================
async def generate_humaneval_solutions(model, dataset, n_samples: int):
    """
    Generate raw solution strings for each problem.
    This function is required by run_experiment.py
    """
    all_results = []
    for problem in dataset:
        prompt = problem["prompt"]

        samples = await generate_code_samples(model, prompt, n_samples)
        all_results.append(
            {
                "task_id": problem["task_id"],
                "entry_point": problem["entry_point"],
                "samples": samples,
                "test": problem["test"],
            }
        )
    return all_results


# ================================================================
# Required export: run_humaneval_evaluation
# ================================================================
async def run_humaneval_evaluation(model, dataset, n_samples: int):
    summary = []

    for problem in dataset:
        samples = await generate_code_samples(model, problem["prompt"], n_samples)

        res = evaluate_problem_passk(
            entry_point=problem["entry_point"],
            samples=samples,
            test_code=problem["test"],
            k=n_samples,
        )

        summary.append({
            "task_id": problem["task_id"],
            "pass@k": res["pass@k"],
            "results": res["results"],
            "num_total": res["num_total"],
            "num_correct": res["num_correct"],
        })

    return summary


# ================================================================
# Required export: run_humaneval_multi_agent
# ================================================================
async def run_humaneval_multi_agent(team, dataset, n_samples: int):
    """
    Multi-agent evaluation for MASWE.
    """
    summary = []

    for problem in dataset:
        task = {
            "type": "code_generation_task",
            "prompt": problem["prompt"],
            "test_code": problem["test"],
            "entry_point": problem["entry_point"],
            "n_samples": n_samples,
        }

        response = await team.run(task)

        samples = response["samples"]
        res = evaluate_problem_passk(
            entry_point=problem["entry_point"],
            samples=samples,
            test_code=problem["test"],
            k=n_samples,
        )

        summary.append(
            {
                "task_id": problem["task_id"],
                "pass@k": res["pass@k"],
                "num_total": res["num_total"],
                "num_correct": res["num_correct"],
                "results": res["results"],
            }
        )

    return summary

# ================================================================
# Backward compatibility: evaluate_humaneval_solutions
# ================================================================
def evaluate_humaneval_solutions(all_results, k=3):
    """
    Evaluate a list of:
        {
            "task_id": str,
            "entry_point": str,
            "samples": [code_str, ...],
            "test": test_code
        }

    Returns:
        [
            {
                "task_id": ...,
                "pass@k": float,
                "num_correct": int,
                "num_total": int,
                "results": [True/False,...]
            },
            ...
        ]
    """
    summary = []

    for item in all_results:
        entry_point = item["entry_point"]
        samples = item["samples"]
        test_code = item["test"]

        eval_res = evaluate_problem_passk(
            entry_point=entry_point,
            samples=samples,
            test_code=test_code,
            k=k,
        )

        summary.append(
            {
                "task_id": item["task_id"],
                "pass@k": eval_res["pass@k"],
                "num_correct": eval_res["num_correct"],
                "num_total": eval_res["num_total"],
                "results": eval_res["results"],
            }
        )

    return summary
