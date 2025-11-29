import asyncio
import argparse
from datetime import datetime

from metagpt.config2 import Config
from metagpt.llm import LLM
from metagpt.team import Team
from metagpt.roles import ProductManager, Architect, Engineer
from metagpt.configs.llm_config import LLMType


# =============== Ollama Base URL ===============
OLLAMA_BASE_URL = "http://host.docker.internal:11434"


# =============== LOCAL MODEL CONFIG ===============
def get_local_config(model_name: str):
    """Create a config for local Ollama model."""
    cfg = Config.default()

    cfg.llm.model = model_name
    cfg.llm.api_type = LLMType.OLLAMA          # ← Use Enum (must)
    cfg.llm.base_url = OLLAMA_BASE_URL
    cfg.llm.api_key = "ollama"                 # not used, but must not be empty
    cfg.llm.calc_usage = False                 # speed optimization

    return cfg


# =============== CLOUD MODEL CONFIG ===============
def get_cloud_config(model_name: str = "gpt-4.1"):
    cfg = Config.default()

    cfg.llm.model = model_name
    cfg.llm.api_type = LLMType.OPENAI
    cfg.llm.api_key = "YOUR_OPENAI_KEY"

    return cfg


# =============== MAIN PIPELINE ===============
async def run_experiment(mode: str, task: str):
    print(f"\n🧪 STARTING EXPERIMENT | MODE: {mode.upper()} | TASK: {task}")
    print("=" * 60)

    # 1. Build Agents -------------------------------------------------------
    if mode == "local":
        print("💻 Initializing LOCAL Agents (using Ollama)...")

        # PM uses a chat-heavy small model
        pm_conf = get_local_config("qwen2.5:7b-instruct")
        print("   - [PM] Loading qwen2.5:7b-instruct")
        pm = ProductManager()
        pm.llm = LLM(llm_config=pm_conf.llm)

        # Architect: use DeepSeek
        arch_conf = get_local_config("deepseek-coder:6.7b")
        print("   - [Architect] Loading deepseek-coder:6.7b")
        arch = Architect()
        arch.llm = LLM(llm_config=arch_conf.llm)

        # Developer: use Qwen coder
        dev_conf = get_local_config("qwen2.5-coder:7b")
        print("   - [Developer] Loading qwen2.5-coder:7b")
        dev = Engineer()
        dev.llm = LLM(llm_config=dev_conf.llm)

        agents = [pm, arch, dev]

    else:
        print("☁️ Initializing CLOUD Agents (GPT/Claude)...")

        cloud_conf = get_cloud_config("gpt-4.1")
        brain = LLM(llm_config=cloud_conf.llm)

        pm = ProductManager(); pm.llm = brain
        arch = Architect(); arch.llm = brain
        dev = Engineer(); dev.llm = brain

        agents = [pm, arch, dev]

    # 2. Create Team ---------------------------------------------------------
    company = Team()
    company.hire(agents)
    company.invest(investment=10.0)

    start_time = datetime.now()

    print("\n🚀 Running multi-agent pipeline...\n")

    await company.run(idea=task)

    end_time = datetime.now()

    print("=" * 60)
    print(f"✅ DONE in {(end_time - start_time).total_seconds():.2f} seconds")
    print("📂 Output saved under /app/workspace")


# =============== CLI ENTRY ===============
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MASWE Multi-Agent SWE Runner")
    parser.add_argument("--mode", type=str, choices=["local", "cloud"], default="local")
    parser.add_argument("--task", type=str, default="Write a command-line Snake game in Python")

    args = parser.parse_args()

    asyncio.run(run_experiment(args.mode, args.task))
