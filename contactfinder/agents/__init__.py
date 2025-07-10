from .gemini_agent import gemini_agent
from .gpt_serper_agent import gpt_serper_agent

AGENTS = {
    "gemini": gemini_agent,
    "gpt": gpt_serper_agent,
}

def get_agent(agent_name: str = "gemini"):
    """Get agent function by name."""
    if agent_name not in AGENTS:
        raise ValueError(f"Unknown agent: {agent_name}. Available: {list(AGENTS.keys())}")
    return AGENTS[agent_name]

__all__ = ["get_agent", "AGENTS", "gemini_agent", "gpt_serper_agent"]
