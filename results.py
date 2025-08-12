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
    """Save results to CSV and text report with timing and RAG info"""
    
    # Save to CSV with additional RAG columns
    df = pd.DataFrame([
        {
            'question_id': r.question_id,
            'question': r.question,
            'question_type': r.question_type,
            'agent_answer': r.agent_answer,
            'expected_answer': r.expected_answer,
            'is_correct': r.is_correct,
            'confidence': r.confidence_score,
            'reasoning': r.reasoning_analysis,
            'rag_found': r.rag_found,
            'rag_content': r.rag_content
        }
        for r in results.detailed_results
    ])
    
    df.to_csv(output_path, index=False)
    
    # Create detailed text report
    report_path = output_path.replace('.csv', '_report.txt')
    
    with open(report_path, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("FINANCEQA BENCHMARK EVALUATION REPORT\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Dataset: {results.total_questions} questions\n")
        
        # Execution timing with parallel info
        if hasattr(results, 'execution_time'):
            minutes = results.execution_time / 60
            f.write(f"Execution Time: {results.execution_time:.1f} seconds ({minutes:.1f} minutes)\n")
            f.write(f"Average per question: {results.execution_time/results.total_questions:.1f} seconds\n")
            if hasattr(results, 'max_workers'):
                f.write(f"Parallel Workers: {results.max_workers}\n")
                sequential_estimate = results.execution_time * results.max_workers
                f.write(f"Estimated sequential time: {sequential_estimate/60:.1f} minutes\n")
                speedup = sequential_estimate / results.execution_time
                f.write(f"Parallel speedup: {speedup:.1f}x\n")
        
        f.write("\n" + "=" * 50 + "\n")
        f.write("OVERALL RESULTS\n")
        f.write("=" * 50 + "\n")
        f.write(f"Overall Accuracy: {results.overall_accuracy:.1%} ({results.total_correct}/{results.total_questions})\n")
        f.write(f"Paper Baseline: 54.1%\n")
        
        improvement = results.overall_accuracy - 0.541
        f.write(f"vs Baseline: {improvement:+.1%}\n")
        
        f.write("\n" + "=" * 50 + "\n")
        f.write("BREAKDOWN BY QUESTION TYPE\n")
        f.write("=" * 50 + "\n")
        for q_type, accuracy in results.by_type_accuracy.items():
            count = sum(1 for r in results.detailed_results if r.question_type == q_type)
            correct = sum(1 for r in results.detailed_results if r.question_type == q_type and r.is_correct)
            f.write(f"{q_type.replace('_', ' ').title():20}: {accuracy:.1%} ({correct:3d}/{count:3d})\n")
        
        # RAG Analysis
        f.write("\n" + "=" * 50 + "\n")
        f.write("RAG UTILIZATION ANALYSIS\n")
        f.write("=" * 50 + "\n")
        
        # Knowledge source summary
        total_chunks = len(agent.rag.knowledge_chunks)
        hardcoded_chunks = len([c for c in agent.rag.knowledge_chunks if c.get('source') != 'pdf_valuation'])
        pdf_chunks = total_chunks - hardcoded_chunks
        
        f.write(f"Knowledge Sources:\n")
        f.write(f"  - Hardcoded financial rules: {hardcoded_chunks} chunks\n")
        if pdf_chunks > 0:
            f.write(f"  - PDF textbook content: {pdf_chunks} chunks\n")
            f.write(f"  - PDF path: {agent.rag.textbook_path}\n")
        else:
            f.write(f"  - PDF textbook: Not loaded\n")
        f.write(f"  - Total knowledge chunks: {total_chunks}\n\n")
        
        total_with_rag = sum(1 for r in results.detailed_results if r.rag_found)
        rag_percentage = total_with_rag / results.total_questions * 100
        f.write(f"Questions with RAG snippets: {total_with_rag}/{results.total_questions} ({rag_percentage:.1f}%)\n")
        
        # RAG accuracy analysis
        rag_correct = sum(1 for r in results.detailed_results if r.rag_found and r.is_correct)
        no_rag_correct = sum(1 for r in results.detailed_results if not r.rag_found and r.is_correct)
        
        if total_with_rag > 0:
            rag_accuracy = rag_correct / total_with_rag
            f.write(f"Accuracy with RAG: {rag_accuracy:.1%} ({rag_correct}/{total_with_rag})\n")
        
        total_without_rag = results.total_questions - total_with_rag
        if total_without_rag > 0:
            no_rag_accuracy = no_rag_correct / total_without_rag
            f.write(f"Accuracy without RAG: {no_rag_accuracy:.1%} ({no_rag_correct}/{total_without_rag})\n")
        
        # Question type distribution
        f.write("\n" + "=" * 50 + "\n")
        f.write("QUESTION TYPE DISTRIBUTION\n")
        f.write("=" * 50 + "\n")
        for q_type in ['basic_tactical', 'assumption_tactical', 'conceptual']:
            count = sum(1 for r in results.detailed_results if r.question_type == q_type)
            percentage = count / results.total_questions * 100
            f.write(f"{q_type.replace('_', ' ').title():20}: {count:3d} ({percentage:.1f}%)\n")
        
        # Failed cases analysis
        failures = [r for r in results.detailed_results if not r.is_correct]
        f.write("\n" + "=" * 50 + "\n")
        f.write(f"FAILED CASES ANALYSIS ({len(failures)} failures)\n")
        f.write("=" * 50 + "\n")
        
        for i, fail in enumerate(failures[:5], 1):  # Show first 5 failures
            f.write(f"\n{i}. {fail.question_id} ({fail.question_type})\n")
            f.write(f"   Question: {fail.question[:100]}{'...' if len(fail.question) > 100 else ''}\n")
            f.write(f"   Expected: {fail.expected_answer}\n")
            f.write(f"   Agent:    {fail.agent_answer}\n")
            f.write(f"   RAG Used: {'Yes' if fail.rag_found else 'No'}\n")
            f.write(f"   Reason:   {fail.reasoning_analysis}\n")
        
        if len(failures) > 5:
            f.write(f"\n... and {len(failures) - 5} more failures (see CSV for complete list)\n")
    
    # Console output (simplified)
    print(f"\n{'='*50}")
    print(f"FINANCEQA BENCHMARK RESULTS")
    print(f"{'='*50}")
    print(f"Dataset: {results.total_questions} questions")
    print(f"Overall Accuracy: {results.overall_accuracy:.1%} ({results.total_correct}/{results.total_questions})")
    print(f"Paper Baseline: 54.1%")
    
    improvement = results.overall_accuracy - 0.541
    print(f"vs Baseline: {improvement:+.1%}")
    
    print(f"\nBy Question Type:")
    for q_type, accuracy in results.by_type_accuracy.items():
        count = sum(1 for r in results.detailed_results if r.question_type == q_type)
        correct = sum(1 for r in results.detailed_results if r.question_type == q_type and r.is_correct)
        print(f"  {q_type.replace('_', ' ').title()}: {accuracy:.1%} ({correct}/{count})")
    
    print(f"\nRAG Usage: {total_with_rag}/{results.total_questions} questions ({rag_percentage:.1f}%)")
    
    print(f"\nFiles saved:")
    print(f"  CSV: {output_path}")
    print(f"  Report: {report_path}")
    
    # Show sample failures
    failures = [r for r in results.detailed_results if not r.is_correct][:3]
    if failures:
        print(f"\nSample Failed Cases:")
        for i, fail in enumerate(failures, 1):
            print(f"\n{i}. {fail.question}")
            print(f"   Expected: {fail.expected_answer}")
            print(f"   Got: {fail.agent_answer}")
    
    if hasattr(results, 'execution_time'):
        print(f"Execution Time: {results.execution_time/60:.1f} minutes")
