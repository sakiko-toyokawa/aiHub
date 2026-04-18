"""AI Summarizer module for the AI Knowledge Hub.

This module provides LLM-based content summarization with multi-provider support.
"""

from .llm_client import LLMClient, SummaryResult

__all__ = ['LLMClient', 'SummaryResult']
