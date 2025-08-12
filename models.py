"""
Data models and enums for the FinanceQA Agent.
"""

from typing import Dict, List
from dataclasses import dataclass
from enum import Enum


class QuestionType(Enum):
    BASIC_TACTICAL = "basic_tactical"
    ASSUMPTION_TACTICAL = "assumption_tactical"  
    CONCEPTUAL = "conceptual"


@dataclass
class EvaluationResult:
    question_id: str
    question: str
    agent_answer: str
    expected_answer: str
    is_correct: bool
    confidence_score: float
    question_type: str
    reasoning_analysis: str = ""
    rag_found: bool = False
    rag_content: str = ""


@dataclass
class BenchmarkResults:
    overall_accuracy: float
    by_type_accuracy: Dict[str, float]
    detailed_results: List[EvaluationResult]
    total_questions: int
    total_correct: int
