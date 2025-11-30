#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
import logging
from typing import List, Optional

from metagpt.environment import Environment
from metagpt.schema import Message   # ← only Message (your schema has no RoleMessage)
from metagpt.roles import Role

logger = logging.getLogger(__name__)


class Team:
    """Team orchestrates multiple roles in an environment."""

    def __init__(
        self,
        roles: List[Role],
        env: Environment,
        max_round: int = 10,
    ):
        self.roles = roles
        self.env = env
        self.max_round = max_round

        # Register roles into environment
        for role in self.roles:
            self.env.add_role(role)

    async def _run_one_turn(self) -> Optional[Message]:
        """Run one round of multi-agent reasoning."""
        try:
            # Let env route messages & schedule roles
            await self.env.step()

            if not self.env.history:
                return None

            last_msg = self.env.history[-1]

            # Safety: wrap string as Message
            if isinstance(last_msg, str):
                last_msg = Message(content=str(last_msg), role="system")

            return last_msg

        except Exception as e:
            logger.error(f"❌ Team turn failed: {e}")
            # Do NOT infinite loop — stop immediately
            return None

    async def run(self) -> List[Message]:
        """Run full team workflow for max_round turns."""
        logger.info("🚀 Team starting workflow...")
        outputs = []

        for i in range(self.max_round):
            logger.info(f"🔁 Round {i+1}/{self.max_round}")

            msg = await self._run_one_turn()

            if msg is None:
                logger.info("⚠️ No more messages, stopping.")
                break

            outputs.append(msg)

        logger.info("🏁 Team finished.")
        return outputs
