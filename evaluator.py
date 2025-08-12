"""
Numerical evaluator for financial answers.
"""

from typing import Tuple
import logging
import openai
try:
    from .utils import retry_with_exponential_backoff
except ImportError:
    from utils import retry_with_exponential_backoff

logger = logging.getLogger(__name__)


class NumericalEvaluator:
    """Simplified binary numerical evaluation"""
    
    def __init__(self, client: openai.OpenAI, model: str = "gpt-4o"):
        self.client = client
        self.model = model
        
    def evaluate_answer(self, question: str, agent_answer: str, expected_answer: str) -> Tuple[bool, str]:
        """Evaluate with exact match requirement (allowing for rounding)"""
        
        prompt = f"""Evaluate exactness of financial answers:

Q: {question}
EXPECTED: {expected_answer}  
AGENT: {agent_answer}

RULES: Exact match required. Rounding OK (123.4=123). Unit equivalents OK (12.5%=0.125, 1.5B=1500M).

FORMAT:
CORRECTNESS: [CORRECT/INCORRECT]
REASON: [Brief explanation]"""
        
        try:
            def make_api_call():
                return self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                    max_tokens=100
                )
            
            response = retry_with_exponential_backoff(make_api_call)
            result = response.choices[0].message.content
            
            # Fix: Check for exact CORRECT/INCORRECT status, not substring match
            first_line = result.split('\n')[0].upper()
            if "INCORRECT" in first_line:
                is_correct = False
            elif "CORRECT" in first_line:
                is_correct = True
            else:
                # Fallback: look for the exact pattern
                is_correct = first_line.endswith("CORRECT")
            reason = result.split('REASON:')[-1].strip() if 'REASON:' in result else "Evaluation completed"
            
            return is_correct, reason
            
        except Exception as e:
            logger.error(f"Evaluation error: {e}")
            return False, f"Evaluation failed: {e}"
