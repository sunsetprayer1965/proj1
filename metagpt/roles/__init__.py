#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:43
@Author  : alexanderwu
@File    : __init__.py
"""

# Core roles
from .role import Role
from .product_manager import ProductManager
from .architect import Architect
from .project_manager import ProjectManager

# Engineering roles
from .developer import Developer          # ← your custom developer
from .reviewer import Reviewer            # ← reviewer class
from .engineer import Engineer
from .qa_engineer import QaEngineer

# Other roles
from .searcher import Searcher
from .sales import Sales
from .customer_service import CustomerService

__all__ = [
    "Role",
    "Architect",
    "ProjectManager",
    "ProductManager",
    "Developer",
    "Reviewer",
    "Engineer",
    "QaEngineer",
    "Searcher",
    "Sales",
    "CustomerService",
]
