from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from popa.claude_adapter import ClaudeAdapter


@dataclass
class AgentConfig:
    def get_adapter(self):
        raise NotImplementedError()


class ClaudeConfig(AgentConfig):
    def get_adapter(self):
        return ClaudeAdapter(os.getenv("ANTHROPIC_API_KEY"))


CONFIG_PATH = Path(".popa_config.yaml")


def load_config() -> AgentConfig:
    if not CONFIG_PATH.exists():
        return ClaudeConfig()

    with open(CONFIG_PATH) as f:
        data = json.load(f)

    return AgentConfig(**data)
