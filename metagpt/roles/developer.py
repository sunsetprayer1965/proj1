#!/usr/bin/env python
# -*- coding: utf-8 -*-

from metagpt.roles.engineer import Engineer
from metagpt.actions.write_tasks_dev import WriteTasksDev
from metagpt.actions.write_code_plan import WriteCodePlan
from metagpt.actions.write_code import WriteCode
from metagpt.actions.debug_error import DebugError
from metagpt.actions.project_management import WriteTasks
from metagpt.schema import Message


class Developer(Engineer):
    name: str = "Developer"

    def __init__(self, name: str = "Developer"):
        super().__init__(name=name)

        self.set_actions([
            WriteTasksDev(),
            WriteCodePlan(),
            WriteCode(),
            DebugError(),
        ])

        # Watch PM work so developer can respond to tasks
        self._watch([WriteTasks])

    async def _act(self) -> Message:
        """
        Override Engineer._act to guarantee ALWAYS returning Message.
        MetaGPT old versions do not support RoleMessage.
        """

        raw = await super()._act()

        # If already message -> return it
        if isinstance(raw, Message):
            return raw

        # Otherwise wrap raw string
        return Message(
            content=str(raw),
            role=self.profile,
            cause_by=self._get_current_action(),
            sent_from=self,
        )
