#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/19 17:26
@Author  : alexanderwu
@File    : llm_provider_registry.py
"""
from metagpt.configs.llm_config import LLMConfig, LLMType
from metagpt.provider.base_llm import BaseLLM


class LLMProviderRegistry:
    def __init__(self):
        self.providers = {}

    def register(self, key, provider_cls):
        self.providers[key] = provider_cls

    def get_provider(self, enum: LLMType):
        """get provider instance according to the enum"""
        return self.providers[enum]


def register_provider(key):
    """register provider to registry"""

    def decorator(cls):
        LLM_REGISTRY.register(key, cls)
        return cls

    return decorator


def create_llm_instance(config: LLMConfig) -> BaseLLM:
    """get the default llm provider"""

    # Lazy-load providers that are not imported elsewhere
    from metagpt.configs.llm_config import LLMType as _LLMType

    # 如果是 Ollama，但是还没注册，就强制 import 一次，
    # 触发 @register_provider(LLMType.OLLAMA)
    if config.api_type == _LLMType.OLLAMA and _LLMType.OLLAMA not in LLM_REGISTRY.providers:
        from metagpt.provider import ollama_api  # noqa: F401

    return LLM_REGISTRY.get_provider(config.api_type)(config)


# Registry instance
LLM_REGISTRY = LLMProviderRegistry()
