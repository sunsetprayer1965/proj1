#!/usr/bin/env python
# -*- coding: utf-8 -*-

from metagpt.actions.action import Action
from metagpt.actions.action_output import ActionOutput
from metagpt.logs import logger
from metagpt.schema import Document
import json


class WriteTasksDev(Action):
    name: str = "WriteTasksDev"

    async def run(self, with_messages):
        design_docs = self.repo.docs.system_design.docs

        if not design_docs:
            logger.warning("No design document found. Cannot generate tasks.")
            return ActionOutput(content="", instruct_content=None)

        # Developer should output actual file names to be coded
        task_files = [
            "main.py",
            "snake.py",
            "game_engine.py",
            "renderer.py",
        ]

        task_json = {
            "task_list": task_files
        }

        # Save into docs/tasks
        task_doc = Document(
            filename="tasks.json",
            content=json.dumps(task_json, indent=4),
            root_path=self.repo.root_path,
        )

        # save for project manager + developer
        for _, design_doc in design_docs.items():
            await self.repo.docs.task.save_doc(
                doc=task_doc,
                dependencies={design_doc.root_relative_path},
            )

        logger.info(f"Generated {len(task_files)} coding tasks: {task_files}")

        return ActionOutput(content=json.dumps(task_json), instruct_content=task_json)
