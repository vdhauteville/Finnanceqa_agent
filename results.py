"""
Results handling and reporting for the FinanceQA Agent.
"""

import pandas as pd
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import BenchmarkResults
    from .agent import FinanceQAAgent


def save_results(agent: 'FinanceQAAgent', results: 'BenchmarkResults', output_path: str):
    """Save results to CSV"""
    
    # Save to CSV (removed only rag_found and confidence)
    df = pd.DataFrame([
        {
            'question_id': r.question_id,
            'question': r.question,
            'question_type': r.question_type,
            'agent_answer': r.agent_answer,
            'expected_answer': r.expected_answer,
            'is_correct': r.is_correct,
            'reasoning': r.reasoning_analysis,
            'rag_content': r.rag_content
        }
        for r in results.detailed_results
    ])
    
    df.to_csv(output_path, index=False)
    
    # Simple console output with timing
    print(f"Accuracy: {results.overall_accuracy:.1%} ({results.total_correct}/{results.total_questions})")
    
    for q_type, accuracy in results.by_type_accuracy.items():
        count = sum(1 for r in results.detailed_results if r.question_type == q_type)
        print(f"{q_type}: {accuracy:.1%} ({count} questions)")
    
    # Execution timing analysis
    if hasattr(results, 'execution_time'):
        execution_time = results.execution_time
        minutes = execution_time / 60
        avg_per_question = execution_time / results.total_questions
        
        print(f"\nExecution Time: {execution_time:.1f}s ({minutes:.1f} minutes)")
        print(f"Average per question: {avg_per_question:.1f}s")
        
        if hasattr(results, 'max_workers'):
            workers = results.max_workers
            print(f"Parallel workers: {workers}")
            if workers > 1:
                sequential_estimate = execution_time * workers
                speedup = sequential_estimate / execution_time
                print(f"Estimated speedup: {speedup:.1f}x vs sequential")

