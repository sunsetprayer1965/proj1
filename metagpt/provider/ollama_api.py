#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from requests import ConnectionError
from tenacity import (
    retry, stop_after_attempt, wait_random_exponential,
    retry_if_exception_type, after_log
)

from metagpt.configs.llm_config import LLMConfig, LLMType
from metagpt.const import LLM_API_TIMEOUT
from metagpt.logs import logger, log_llm_stream
from metagpt.provider.base_llm import BaseLLM
from metagpt.provider.general_api_requestor import GeneralAPIRequestor
from metagpt.provider.llm_provider_registry import register_provider
from metagpt.provider.openai_api import log_and_reraise
from metagpt.utils.cost_manager import TokenCostManager


@register_provider(LLMType.OLLAMA)
class OllamaLLM(BaseLLM):

    def __init__(self, config: LLMConfig):
        assert config.base_url, "ollama base url is required!"

        self.model = config.model
        self.config = config
        self.client = GeneralAPIRequestor(base_url=config.base_url)

        self.http_method = "post"
        self.suffix_url = "/api/generate"
        self._cost_manager = TokenCostManager()

    def _payload(self, messages, stream=False):
        """Convert OpenAI-style messages into a string prompt."""
        prompt = ""
        for m in messages:
            if m["role"] == "system":
                prompt += f"[SYSTEM] {m['content']}\n"
            elif m["role"] == "user":
                prompt += f"{m['content']}\n"
            elif m["role"] == "assistant":
                prompt += f"{m['content']}\n"

        return {
            "model": self.model,
            "prompt": prompt,
            "stream": stream,
            "options": {"temperature": 0.2}
        }
    def _update_costs(self, usage: dict):
        """Update token usage cost (MetaGPT expects this function)."""
        # Ollama does not provide token cost; we only store raw counts.
        try:
            prompt_tokens = int(usage.get("prompt_tokens", 0))
            completion_tokens = int(usage.get("completion_tokens", 0))
        except Exception:
            prompt_tokens = 0
            completion_tokens = 0

        if hasattr(self, "_cost_manager") and self._cost_manager:
            try:
                self._cost_manager.update_cost(prompt_tokens, completion_tokens, getattr(self, "model", "ollama"))
            except Exception:
                pass

    # -------------------
    # Non-Stream
    # -------------------
    async def _achat_completion(self, messages):
        """One-shot non-stream completion"""
        payload = self._payload(messages, stream=False)

        resp, _, _ = await self.client.arequest(
            method=self.http_method,
            url=self.suffix_url,
            params=payload,
            request_timeout=LLM_API_TIMEOUT,
        )

        text = resp.decode("utf-8")
        data = json.loads(text)

        usage = {
            "prompt_tokens": data.get("prompt_eval_count", 0),
            "completion_tokens": data.get("eval_count", 0)
        }
        self._update_costs(usage)

        return data.get("response", "")

    # -------------------
    # Stream
    # -------------------
    async def _achat_completion_stream(self, messages):
        payload = self._payload(messages, stream=True)

        stream_resp, _, _ = await self.client.arequest(
            method=self.http_method,
            url=self.suffix_url,
            stream=True,
            params=payload,
            request_timeout=LLM_API_TIMEOUT,
        )

        full = []
        total_usage = {}

        async for raw in stream_resp:
            line = raw.decode("utf-8").strip()

            if not line:
                continue

            try:
                data = json.loads(line)
            except:
                continue

            # token
            if "response" in data and not data.get("done", False):
                token = data["response"]
                full.append(token)
                log_llm_stream(token)

            # final stats
            if data.get("done", False):
                total_usage = {
                    "prompt_tokens": data.get("prompt_eval_count", 0),
                    "completion_tokens": data.get("eval_count", 0)
                }

        log_llm_stream("\n")
        self._update_costs(total_usage)

        return "".join(full)

    # main entry
    async def acompletion(self, messages):
        return await self._achat_completion(messages)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_random_exponential(min=1, max=60),
        retry=retry_if_exception_type(ConnectionError),
        after=after_log(logger, logger.level("WARNING").name),
        retry_error_callback=log_and_reraise,
    )
    async def acompletion_text(self, messages, stream=False, timeout=3):
        if stream:
            return await self._achat_completion_stream(messages)
        return await self._achat_completion(messages)
