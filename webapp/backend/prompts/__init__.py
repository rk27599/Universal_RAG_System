"""
Prompt Templates for RAG System

Provides different prompt strategies for various use cases:
- CoT (Chain-of-Thought): Step-by-step reasoning
- Extractive: Direct quotes only
- Citation: Citation-aware responses (Material Studio expert)
"""

from .cot_template import COT_TEMPLATE, build_cot_prompt
from .extractive_template import EXTRACTIVE_TEMPLATE, build_extractive_prompt
from .citation_template import CITATION_TEMPLATE, build_citation_prompt

__all__ = [
    'COT_TEMPLATE',
    'EXTRACTIVE_TEMPLATE',
    'CITATION_TEMPLATE',
    'build_cot_prompt',
    'build_extractive_prompt',
    'build_citation_prompt',
]
