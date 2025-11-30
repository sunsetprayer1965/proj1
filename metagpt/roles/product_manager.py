#!/usr/bin/env python
# -*- coding: utf-8 -*-

from metagpt.roles.role import Role, RoleReactMode
from metagpt.actions.prepare_documents import PrepareDocuments
from metagpt.actions.add_requirement import UserRequirement
from metagpt.actions.write_prd import WritePRD


class ProductManager(Role):
    """负责从用户需求到 PRD 的 PM"""

    name: str = "Alice"
    profile: str = "Product Manager"
    goal: str = "Clarify user requirements and write PRD"
    constraints: str = "Write clear, structured PRD for downstream roles."

    def __init__(self, **data):
        super().__init__(**data)

        # 监听 Human Requirement + PrepareDocuments 完成结果
        self._watch([UserRequirement, PrepareDocuments])

        # 设置动作（按固定顺序）
        self.set_actions([
            PrepareDocuments,   # state 0
            WritePRD,           # state 1
        ])

        # 关键：不让 LLM 决定 state（避免输出 2）
        self._set_react_mode(
            react_mode=RoleReactMode.BY_ORDER,
            max_react_loop=99,   # 在一次 _react 中执行两个动作
        )
