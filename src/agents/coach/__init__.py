"""Agent-Coach — dialogue analysis and feedback generation."""

from agents.coach.adapter import LLMCoachAdapter
from agents.coach.agent import CoachAgent
from agents.coach.llm_agent import LLMCoachAgent

__all__ = [
    "CoachAgent",
    "LLMCoachAdapter",
    "LLMCoachAgent",
]
