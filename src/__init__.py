"""
LLM Dependency Bot - Autonomous AI agent for dependency management.

This package provides an intelligent dependency management bot powered by
Claude 3.5 Sonnet that analyzes, decides, and acts on dependency update PRs.
"""

__version__ = "1.0.0"
__author__ = "LLM Dependency Bot Contributors"
__license__ = "MIT"

from src.agent import LLMDependencyBot, MergeDecision, PRContext, RiskLevel

__all__ = [
    "LLMDependencyBot",
    "RiskLevel",
    "MergeDecision",
    "PRContext",
]
