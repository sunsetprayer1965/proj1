#!/usr/bin/env python
# -*- coding: utf-8 -*-

from metagpt.roles.qa_engineer import QaEngineer
from metagpt.actions.write_test import WriteTest
from metagpt.actions.write_code_review import WriteCodeReview

class Reviewer(QaEngineer):
    name: str = "Reviewer"

    def __init__(self, name: str = "Reviewer"):
        super().__init__(name=name)

        self.set_actions([
            WriteTest(),
            WriteCodeReview(filename="code_review.md"),  # 关键改动：补上 filename
        ])
