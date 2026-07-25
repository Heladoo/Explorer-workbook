"""The five agents of the pipeline.

Each agent owns one responsibility and communicates only through the models in
:mod:`src.models` — knowledge in, plan out, drafts out, prompts out, docs out.
"""

from src.agents.destination_agent import (
    DestinationKnowledgeAgent,
    FileKnowledgeProvider,
    HeuristicKnowledgeProvider,
    KnowledgeProvider,
    LLMKnowledgeProvider,
    build_knowledge_agent,
)
from src.agents.markdown_generator import MarkdownGenerator
from src.agents.planner import WorkbookPlanner
from src.agents.prompt_generator import PromptGenerator

__all__ = [
    "DestinationKnowledgeAgent",
    "FileKnowledgeProvider",
    "HeuristicKnowledgeProvider",
    "KnowledgeProvider",
    "LLMKnowledgeProvider",
    "MarkdownGenerator",
    "PromptGenerator",
    "WorkbookPlanner",
    "build_knowledge_agent",
]
