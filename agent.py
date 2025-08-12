"""
Main FinanceQA Agent class.
"""

import time
import re
import logging
import pandas as pd
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import openai

try:
    from .models import EvaluationResult, BenchmarkResults
    from .rag import FinancialRAG
    from .evaluator import NumericalEvaluator
    from .utils import retry_with_exponential_backoff
except ImportError:
    from models import EvaluationResult, BenchmarkResults
    from rag import FinancialRAG
    from evaluator import NumericalEvaluator
    from utils import retry_with_exponential_backoff

logger = logging.getLogger(__name__)


class FinanceQAAgent:
    """Simplified AI Agent for FinanceQA benchmark"""
    
    def __init__(self, openai_api_key: str, textbook_path: str = None):
        openai.api_key = openai_api_key
        self.client = openai.OpenAI()
        self.rag = FinancialRAG(textbook_path)
        self.evaluator = NumericalEvaluator(self.client)
    
    def answer_question(self, question: str, context: str = "") -> Dict:
        """Combined classification and reasoning in single API call"""
        # Get relevant methodology
        rag_results = self.rag.query(question, top_k=5) if context.strip() else []
        methodology = "\n".join([r['text'] for r in rag_results])
        rag_found = len(rag_results) > 0
        
        # Single combined prompt that does classification + reasoning
        system_prompt = """You are a senior financial analyst. You must first classify the question type, then answer it accordingly.

QUESTION TYPES:
- CONCEPTUAL: No financial context provided, requires theoretical knowledge
- BASIC_TACTICAL: Context contains sufficient information to answer directly
- ASSUMPTION_TACTICAL: Context provided but insufficient, requires reasonable assumptions"""
        
        user_prompt = f"""
CONTEXT: {context if context.strip() else "No context provided"}

METHODOLOGY: {methodology if methodology else "No specific methodology retrieved"}

QUESTION: {question}

INSTRUCTIONS:
1. First, classify this question as: CONCEPTUAL, BASIC_TACTICAL, or ASSUMPTION_TACTICAL
2. Then answer according to your classification using chain-of-thought reasoning:

   - If CONCEPTUAL: Provide clear theoretical analysis with examples
   - If BASIC_TACTICAL: Extract relevant numbers, show formula, calculate step-by-step
   - If ASSUMPTION_TACTICAL: State reasonable assumptions based on industry standards, then calculate

REASONING APPROACH:
1. State the relevant formula
2. Extract numbers from context  
3. Show calculation steps
4. Convert units as needed (M/B, %/decimal)
5. Provide final answer with units

IMPORTANT: GAAP vs NON-GAAP CONSIDERATIONS:
- First determine if the financial measure is GAAP or non-GAAP
- GAAP measures: Use standard accounting principles and formulas
- Non-GAAP measures: May require adjustments (exclude one-time items, stock compensation, etc.)
- When calculating non-GAAP metrics, clearly state what adjustments are being made
- Examples: Adjusted EBITDA, Core earnings, Normalized revenue

FORMAT YOUR RESPONSE EXACTLY AS:
CLASSIFICATION: [CONCEPTUAL/BASIC_TACTICAL/ASSUMPTION_TACTICAL]
ASSUMPTIONS: [List any assumptions made, or "None" if no assumptions]
CALCULATIONS: [Show step-by-step work, or reasoning for conceptual questions]
FINAL ANSWER: [Your final answer with units/explanation]
"""
        
        # Single API call for both classification and reasoning
        try:
            def make_api_call():
                return self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.1,
                    max_tokens=1200
                )
            
            response = retry_with_exponential_backoff(make_api_call)
            
            answer_text = response.choices[0].message.content
            
            # Extract classification
            class_match = re.search(r'CLASSIFICATION:\s*(\w+)', answer_text, re.IGNORECASE)
            question_type = class_match.group(1).lower() if class_match else "basic_tactical"
            
            # Extract final answer
            final_answer_match = re.search(r'FINAL ANSWER:\s*(.+?)(?:\n|$)', answer_text, re.IGNORECASE)
            final_answer = final_answer_match.group(1).strip() if final_answer_match else answer_text.split('\n')[-1].strip()
            
            # Extract assumptions
            assumptions_match = re.search(r'ASSUMPTIONS:\s*(.+?)(?=\n[A-Z]|\n\n|$)', answer_text, re.DOTALL | re.IGNORECASE)
            assumptions = assumptions_match.group(1).strip() if assumptions_match else ""
            
            return {
                'answer': final_answer,
                'full_response': answer_text,
                'assumptions': assumptions,
                'question_type': question_type,
                'confidence': 0.8,
                'rag_found': rag_found,
                'rag_content': methodology if rag_found else ""
            }
            
        except Exception as e:
            logger.error(f"Error processing question: {e}")
            return {
                'answer': f"Error: {e}",
                'full_response': f"Processing failed: {e}",
                'assumptions': "",
                'question_type': "error",
                'confidence': 0.0,
                'rag_found': False,
                'rag_content': ""
            }
    
    def evaluate_on_dataset(self, csv_path: str, subset_size: Optional[int] = None, 
                          random_subset: bool = True, max_workers: int = 2, random_seed: int = 42) -> BenchmarkResults:
        """Evaluate agent on dataset"""
        start_time = time.time()
        
        # Load dataset
        df = pd.read_csv(csv_path)
        if subset_size and subset_size < len(df):
            df = df.sample(n=subset_size, random_state=random_seed) if random_subset else df.head(subset_size)
        
        # Prepare question data
        question_data = []
        for idx, row in df.iterrows():
            context = '' if pd.isna(row.get('context', '')) else str(row.get('context', ''))
            q_type = 'basic_tactical' if context.strip() else 'conceptual'
            
            question_data.append({
                'question_id': f"q_{idx}",
                'question': str(row['question']),
                'context': context,
                'expected': str(row['answer']),
                'q_type': q_type
            })
        
        # Process questions in parallel
        results = []
        completed_count = 0
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_data = {executor.submit(self._process_single_question, data): data for data in question_data}
            
            for future in as_completed(future_to_data):
                try:
                    result = future.result()
                    results.append(result)
                    completed_count += 1
                    
                    # Log progress every 10 completions
                    if completed_count % 10 == 0 or completed_count == len(question_data):
                        current_accuracy = sum(1 for r in results if r.is_correct) / len(results)
                        elapsed = time.time() - start_time
                        logger.info(f"Progress: {completed_count}/{len(question_data)} - "
                                  f"Accuracy: {current_accuracy:.1%} - "
                                  f"Elapsed: {elapsed:.1f}s")
                
                except Exception as e:
                    # Skip failed questions
                    completed_count += 1
                    continue
        
        # Calculate metrics
        total = len(results)
        correct = sum(1 for r in results if r.is_correct)
        overall_accuracy = correct / total if total > 0 else 0
        
        # By-type accuracy
        type_counts = {}
        type_correct = {}
        for r in results:
            q_type = r.question_type
            type_counts[q_type] = type_counts.get(q_type, 0) + 1
            if r.is_correct:
                type_correct[q_type] = type_correct.get(q_type, 0) + 1
        
        by_type_accuracy = {q: type_correct.get(q, 0) / type_counts[q] for q in type_counts}
        
        # Store execution time
        execution_time = time.time() - start_time
        
        benchmark_results = BenchmarkResults(
            overall_accuracy=overall_accuracy,
            by_type_accuracy=by_type_accuracy,
            detailed_results=results,
            total_questions=total,
            total_correct=correct
        )
        
        # Add execution time for reporting
        benchmark_results.execution_time = execution_time
        benchmark_results.max_workers = max_workers
        
        return benchmark_results
    
    def _process_single_question(self, data: Dict) -> EvaluationResult:
        """Process a single question"""
        response = self.answer_question(data['question'], data['context'])
        is_correct, reasoning = self.evaluator.evaluate_answer(data['question'], response['answer'], data['expected'])
        
        return EvaluationResult(
            question_id=data['question_id'],
            question=data['question'],
            agent_answer=response['answer'],
            expected_answer=data['expected'],
            is_correct=is_correct,
            confidence_score=response['confidence'],
            question_type=data['q_type'],
            reasoning_analysis=reasoning,
            rag_found=response['rag_found'],
            rag_content=response['rag_content']
        )
