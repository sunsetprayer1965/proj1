#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Lightweight agent-level logging & workflow tracing utilities for MASWE.

This module does NOT depend on MetaGPT internals; it just provides a simple
filesystem-based logger that other parts of the system can call into.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Any, Dict, Optional, List


DEFAULT_LOG_BASE = os.environ.get("MASWE_AGENT_LOG_DIR", "/app/workspace/agent_logs")


def _now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="milliseconds") + "Z"


@dataclass
class TraceEvent:
    ts: str
    type: str
    role: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)


class AgentLogger:
    """
    Filesystem-based logger for:
      - per-role logs (pm / architect / dev / coord / reviewer)
      - LLM calls (JSONL)
      - workflow trace events (JSON list in trace.json)
    """

    def __init__(self, run_id: str, base_dir: str = DEFAULT_LOG_BASE) -> None:
        self.run_id = run_id
        self.base_dir = os.path.abspath(base_dir)
        self.run_dir = os.path.join(self.base_dir, self.run_id)

        os.makedirs(self.run_dir, exist_ok=True)

        # lazily written, no long-lived file handles
        self._trace_events: List[TraceEvent] = []

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _write_line(self, filename: str, record: Dict[str, Any]) -> None:
        path = os.path.join(self.run_dir, filename)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def _append_trace(self, event: TraceEvent) -> None:
        self._trace_events.append(event)
        # overwrite full trace.json each time – simpler and logs are small
        path = os.path.join(self.run_dir, "trace.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump([asdict(e) for e in self._trace_events], f, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    # role logs
    # ------------------------------------------------------------------
    def log_role(self, role: str, message: str, **extra: Any) -> None:
        rec = {"ts": _now_iso(), "role": role, "message": message}
        rec.update(extra)
        fname = {
            "pm": "pm.log",
            "product_manager": "pm.log",
            "architect": "architect.log",
            "coord": "coord.log",
            "coordinator": "coord.log",
            "project_manager": "coord.log",
            "dev": "dev.log",
            "developer": "dev.log",
            "qa": "reviewer.log",
            "reviewer": "reviewer.log",
        }.get(role, f"{role}.log")
        self._write_line(fname, rec)

    def log_pm(self, message: str, **extra: Any) -> None:
        self.log_role("pm", message, **extra)

    def log_architect(self, message: str, **extra: Any) -> None:
        self.log_role("architect", message, **extra)

    def log_coord(self, message: str, **extra: Any) -> None:
        self.log_role("coord", message, **extra)

    def log_dev(self, message: str, **extra: Any) -> None:
        self.log_role("dev", message, **extra)

    def log_reviewer(self, message: str, **extra: Any) -> None:
        self.log_role("reviewer", message, **extra)

    # ------------------------------------------------------------------
    # LLM calls
    # ------------------------------------------------------------------
    def log_llm_call(
        self,
        role: str,
        prompt: str,
        completion: str,
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None,
        **meta: Any,
    ) -> None:
        rec: Dict[str, Any] = {
            "ts": _now_iso(),
            "role": role,
            "prompt": prompt,
            "completion": completion,
        }
        if prompt_tokens is not None:
            rec["prompt_tokens"] = int(prompt_tokens)
        if completion_tokens is not None:
            rec["completion_tokens"] = int(completion_tokens)
        if meta:
            rec["meta"] = meta
        self._write_line("llm_calls.jsonl", rec)

    # ------------------------------------------------------------------
    # workflow trace
    # ------------------------------------------------------------------
    def trace_event(self, event_type: str, role: Optional[str] = None, **data: Any) -> None:
        ev = TraceEvent(ts=_now_iso(), type=event_type, role=role, data=data or {})
        self._append_trace(ev)

    # ------------------------------------------------------------------
    # convenience
    # ------------------------------------------------------------------
    @classmethod
    def from_cli_args(cls, args: Any) -> Optional["AgentLogger"]:
        """Create logger from argparse.Namespace (expects log_agent & run_id)."""
        enable = getattr(args, "log_agent", False)
        if not enable:
            return None
        run_id = getattr(args, "run_id", None) or datetime.utcnow().strftime("%Y%m%d%H%M%S")
        return cls(run_id=run_id)
        # ------------------------------------------------------------------
    # global logger API (required by run_experiment.py)
    # ------------------------------------------------------------------
    _GLOBAL_LOGGER = None

    @classmethod
    def init_global(cls, log_dir: str, run_id: Optional[str] = None):
        """
        Initialize a global AgentLogger used across the system.
        Matches how run_experiment.py expects to call logging.
        """
        run_id = run_id or datetime.utcnow().strftime("%Y%m%d%H%M%S")
        cls._GLOBAL_LOGGER = cls(run_id=run_id, base_dir=log_dir)
        return cls._GLOBAL_LOGGER

    @classmethod
    def get_global(cls) -> Optional["AgentLogger"]:
        """
        Return the global logger instance (may be None).
        """
        return cls._GLOBAL_LOGGER


# ----------------------------------------------------------------------
# LLM wrapper
# ----------------------------------------------------------------------
class LLMLoggingWrapper:
    """
    Thin wrapper around a MetaGPT LLM object that logs every acompletion_text call.

    It delegates all unknown attributes to the wrapped LLM, so it should be a
    drop-in replacement.
    """

    def __init__(self, llm: Any, logger: AgentLogger, role: str, run_id: Optional[str] = None) -> None:
        self._llm = llm
        self._logger = logger
        self._role = role
        self._run_id = run_id

    # async text completion (the main API used in MASWE)
    async def acompletion_text(self, messages, *args, **kwargs) -> str:
        # best-effort prompt extraction
        if isinstance(messages, str):
            prompt_text = messages
        else:
            try:
                parts = []
                for m in messages:
                    if isinstance(m, dict):
                        parts.append(str(m.get("content", "")))
                    else:
                        parts.append(str(m))
                prompt_text = "\n".join(parts)
            except Exception:
                prompt_text = str(messages)

        from time import monotonic
        start = monotonic()
        result = await self._llm.acompletion_text(messages, *args, **kwargs)
        latency = monotonic() - start

        def est_tokens(text: str) -> int:
            # very rough approximation: 1 token ~ 4 chars
            return max(1, int(len(text) / 4))

        prompt_tokens = est_tokens(prompt_text)
        completion_tokens = est_tokens(result)

        if self._logger is not None:
            # detailed request/response
            self._logger.log_llm_call(
                role=self._role,
                prompt=prompt_text,
                completion=result,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                run_id=self._run_id,
                latency_sec=latency,
            )
            # lightweight per-role summary line
            self._logger.log_role(
                self._role,
                "llm_call",
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                latency_sec=latency,
            )

        return result

    # fallback: delegate everything else to the underlying LLM
    def __getattr__(self, item: str) -> Any:
        return getattr(self._llm, item)

