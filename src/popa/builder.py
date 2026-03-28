
from popa.agent import Agent
from popa.agent_config import AgentConfig, load_config

def create_agent(
        config: AgentConfig = None,
        system_instructions: str = None, tools=None, cot_logic=None, adapter_config=None
) -> Agent:
    if config is None:
        config = load_config()
    return Agent(
        system_instructions if system_instructions else config.get_system_instructions(),
        adapter_config if adapter_config else config.get_adapter(),
        cot_logic if cot_logic else config.get_cot(),
        tools if tools else config.get_tools()
    )

