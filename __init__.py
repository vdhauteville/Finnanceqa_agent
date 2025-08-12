"""
FinanceQA Agent - A comprehensive financial question answering system.

This package provides an AI-powered agent for answering financial questions
using a combination of hardcoded financial rules and PDF textbook content
via Retrieval Augmented Generation (RAG).
"""

from .agent import FinanceQAAgent
from .rag import FinancialRAG
from .evaluator import NumericalEvaluator
from .models import EvaluationResult, BenchmarkResults, QuestionType
from .results import save_results
from .utils import retry_with_exponential_backoff, setup_logging

__version__ = "1.0.0"
__author__ = "FinanceQA Team"

__all__ = [
    "FinanceQAAgent",
    "FinancialRAG", 
    "NumericalEvaluator",
    "EvaluationResult",
    "BenchmarkResults",
    "QuestionType",
    "save_results",
    "retry_with_exponential_backoff",
    "setup_logging"
]
