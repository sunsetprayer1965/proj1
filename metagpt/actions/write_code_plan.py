#!/usr/bin/env python
# -*- coding: utf-8 -*-

from metagpt.actions.action import Action
from metagpt.actions.action_output import ActionOutput

class WriteCodePlan(Action):
    name: str = "WriteCodePlan"     # ← 必须加类型注解

    async def run(self, with_messages):
        # 从 memory 中提取任务（如果写入过的话）
        tasks = self.get_memory().get("tasks", [])
        if not tasks:
            return ActionOutput(content="", instruct_content=None)

        plan = "\n".join([f"- {t}" for t in tasks])
        return ActionOutput(content=plan, instruct_content=plan)
