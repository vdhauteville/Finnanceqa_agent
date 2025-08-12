"""
Utility functions for the FinanceQA Agent.
"""

import time
import random
import logging
import openai

logger = logging.getLogger(__name__)


def retry_with_exponential_backoff(
    func,
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0
):
    """Retry function with exponential backoff for rate limiting"""
    for attempt in range(max_retries):
        try:
            return func()
        except openai.RateLimitError as e:
            if attempt == max_retries - 1:
                logger.error(f"Max retries ({max_retries}) reached for rate limit")
                raise e
            
            # Exponential backoff with jitter
            delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
            logger.warning(f"Rate limit hit, retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries})")
            time.sleep(delay)
        except Exception as e:
            # For non-rate-limit errors, don't retry
            raise e


def setup_logging(level=logging.INFO):
    """Configure logging for the application"""
    logging.basicConfig(level=level)
    return logging.getLogger(__name__)
