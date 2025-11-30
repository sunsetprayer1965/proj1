#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import asyncio
from datetime import datetime
from pathlib import Path

from metagpt.llm import LLM
from metagpt.configs.llm_config import LLMConfig, LLMType
from metagpt.team import Team
from metagpt.schema import Message
from metagpt.context import Context
from metagpt.utils.git_repository import GitRepository

# Roles
from metagpt.roles.product_manager import ProductManager
from metagpt.roles.architect import Architect
from metagpt.roles.project_manager import ProjectManager
from metagpt.roles.developer import Developer
from metagpt.roles.qa_engineer import QaEngineer


OLLAMA_URL = "http://host.docker.internal:11434"


def build_local_llm(model: str):
    cfg = LLMConfig(
        api_type=LLMType.OLLAMA,
        model=model,
        base_url=OLLAMA_URL,
        api_key="EMPTY",
        temperature=0.1,
        max_tokens=2048,
    )
    return LLM(llm_config=cfg)


# ----------------------------------------------------------------------
# Environment fully compatible with old MetaGPT
# ----------------------------------------------------------------------
class SimpleMessageEnv:
    def __init__(self, project_name="maswe_cli_snake"):
        self.desc = ""
        self.roles = {}
        self.member_addrs = {}
        self.history = ""

        # Prepare project workspace folder
        workspace_root = Path("/app/workspace")
        workspace_root.mkdir(parents=True, exist_ok=True)

        project_root = workspace_root / project_name
        project_root.mkdir(parents=True, exist_ok=True)

        # Create actual GitRepository (REQUIRED by ProjectRepo)
        git_repo = GitRepository(local_path=project_root)

        # Build Context (strictly matching your Context model)
        ctx = Context()
        ctx.git_repo = git_repo       # Needed by Action.repo → ProjectRepo(...)
        ctx.repo = None               # Will be populated by Action.repo property
        ctx.src_workspace = project_root  # developer uses this

        self.context = ctx

    # -------- register roles ----------
    def add_role(self, role):
        self.roles[role.profile] = role
        role.set_env(self)
        role.context = self.context

    # -------- broadcast messages ----------
    def publish_message(self, msg):
        self.history += f"\n{msg}"
        for role in self.roles.values():
            role.put_message(msg)

    # -------- execute each round ----------
    async def step(self):
        tasks = [role.run() for role in self.roles.values()]
        await asyncio.gather(*tasks)

    # -------- required by role.set_env ----------
    def set_addresses(self, role, addresses):
        self.member_addrs[role] = addresses

    def get_addresses(self, role):
        return self.member_addrs.get(role, set())

    # -------- used by WritePRD / ProjectManager ----------
    def role_names(self):
        return list(self.roles.keys())

    def archive(self):
        # GitRepository has archive() — call it
        self.context.git_repo.archive()


# ----------------------------------------------------------------------
# Main MASWE runner
# ----------------------------------------------------------------------
async def run_maswe(mode: str, task: str):
    print(f"\n🧪 STARTING MASWE | MODE: {mode.upper()} | TASK: {task}")
    print("=" * 60)

    pm = ProductManager()
    pm.llm = build_local_llm("qwen2.5:7b-instruct")

    arch = Architect()
    arch.llm = build_local_llm("deepseek-coder:6.7b")

    coord = ProjectManager()
    coord.llm = build_local_llm("qwen2.5:7b-instruct")

    dev = Developer()
    dev.llm = build_local_llm("qwen2.5-coder:7b")

    qa = QaEngineer()
    qa.llm = build_local_llm("qwen2.5-coder:7b")

    roles = [pm, arch, coord, dev, qa]

    env = SimpleMessageEnv()

    team = Team(roles=roles, env=env, max_round=12)

    env.publish_message(Message(role="user", content=task))

    print("🚀 Running multi-agent workflow...\n")
    start = datetime.now()

    await team.run()

    end = datetime.now()
    print("=" * 60)
    print(f"✅ DONE in {(end-start).total_seconds():.2f}s")
    print("📂 Output saved in /app/workspace/maswe_cli_snake\n")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, default="local")
    parser.add_argument("--task", type=str, default="Build a CLI Snake game in Python")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(run_maswe(args.mode, args.task))
