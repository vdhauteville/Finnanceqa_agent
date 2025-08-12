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
    
    def __init__(self, openai_api_key: str, textbook_path: str = None, model: str = "gpt-4o"):
        openai.api_key = openai_api_key
        self.client = openai.OpenAI()
        self.model = model
        self.rag = FinancialRAG(textbook_path)
        self.evaluator = NumericalEvaluator(self.client, model)
    
    def answer_question(self, question: str, context: str = "") -> Dict:
        """Combined classification and reasoning in single API call"""
        # Get relevant methodology (reduced to save tokens)
        rag_results = self.rag.query(question, top_k=2) if context.strip() else []
        methodology = "\n".join([r['text'] for r in rag_results])
        rag_found = len(rag_results) > 0
        
        # Concise prompt with chain-of-thought
        system_prompt = """Financial analyst. Use chain-of-thought reasoning.

TYPES:
- CONCEPTUAL: Theory only  
- BASIC_TACTICAL: Use context data
- ASSUMPTION_TACTICAL: Need assumptions

APPROACH: 1) Classify 2) State formula 3) Extract numbers 4) Calculate 5) Final answer"""
        
        user_prompt = f"""CONTEXT: {context if context.strip() else "None"}
RULES: {methodology if methodology else "None"}
QUESTION: {question}

Use chain-of-thought:
1. Classify question type
2. If GAAP vs non-GAAP, state needed adjustments  
3. State formula → Extract numbers → Calculate → Convert units

FORMAT:
CLASSIFICATION: [type]
ASSUMPTIONS: [list or "None"]
CALCULATIONS: [step-by-step reasoning]
FINAL ANSWER: [answer with units]"""
        
        # Single API call for both classification and reasoning
        try:
            def make_api_call():
                return self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.1,
                    max_tokens=600
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
                          random_subset: bool = True, max_workers: int = 1, random_seed: int = 42,
                          delay_between_requests: float = 0.5) -> BenchmarkResults:
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
        
        # Process questions with rate limiting
        results = []
        completed_count = 0
        
        if max_workers == 1:
            # Serial processing for maximum rate limit safety
            for i, data in enumerate(question_data):
                if i > 0:
                    time.sleep(delay_between_requests)
                
                try:
                    result = self._process_single_question(data)
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
        else:
            # Parallel processing for multiple workers
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_data = {}
                for i, data in enumerate(question_data):
                    if i > 0:
                        time.sleep(delay_between_requests)
                    future_to_data[executor.submit(self._process_single_question, data)] = data
                
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
        
        # Delay between the 2 API calls per question
        time.sleep(0.5)
        
        is_correct, reasoning = self.evaluator.evaluate_answer(data['question'], response['answer'], data['expected'])
        
        # Small delay after both API calls
        time.sleep(0.2)
        
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
