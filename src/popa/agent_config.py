from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from popa.llm_adapter.anthropic import ClaudeAdapter
from popa.cot_logic import CotLogic


@dataclass
class AgentConfig:
    def get_adapter(self):
        raise NotImplementedError()

    def get_system_instructions(self):
        raise NotImplementedError()

    def get_cot(self):
        raise NotImplementedError()

    def get_tools(self):
        raise NotImplementedError()


class DefaultConfig(AgentConfig):
    def get_adapter(self):
        return ClaudeAdapter(os.getenv("ANTHROPIC_API_KEY"))

    def get_system_instructions(self):
        return "You are a helpful agent that uses available tools to solve posed problems."

    def get_cot(self):
        return CotLogic(None)

    def get_tools(self):
        return []

CONFIG_PATH = Path(".popa_config.yaml")


def load_config() -> AgentConfig:
    if not CONFIG_PATH.exists():
        return DefaultConfig()

    with open(CONFIG_PATH) as f:
        data = json.load(f)

    return AgentConfig(**data)
