"""Five pipeline agents."""

from multi_agent_code_factory.agents.architect import run_architect
from multi_agent_code_factory.agents.developer import run_developer
from multi_agent_code_factory.agents.pm import run_pm
from multi_agent_code_factory.agents.qa import run_qa
from multi_agent_code_factory.agents.reviewer import run_reviewer

__all__ = [
    "run_architect",
    "run_developer",
    "run_pm",
    "run_qa",
    "run_reviewer",
]
