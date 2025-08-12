"""
Main entry point for the FinanceQA Agent.
"""

import argparse
import os
import pandas as pd

try:
    # Try relative imports first (when used as package)
    from .agent import FinanceQAAgent
    from .results import save_results
    from .utils import setup_logging
except ImportError:
    # Fall back to direct imports (when run directly)
    from agent import FinanceQAAgent
    from results import save_results
    from utils import setup_logging

logger = setup_logging()





def main():
    """Main function to run the FinanceQA Agent"""
    
    parser = argparse.ArgumentParser(description='Run FinanceQA Agent')
    parser.add_argument('--csv', default='data/financeqa_benchmark.csv', help='Path to CSV file')
    parser.add_argument('--subset', type=int, default=None, help='Number of questions to test (default: all)')
    parser.add_argument('--random', action='store_true', help='Random subset vs first N questions')
    parser.add_argument('--workers', type=int, default=1, help='Number of parallel workers (default: 1, conservative for rate limiting)')
    parser.add_argument('--output', default='results.csv', help='Output file for results')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for reproducible subsets (default: 42)')
    parser.add_argument('--pdf', default='data/Valuation.pdf', help='Path to PDF textbook')
    parser.add_argument('--single-test', action='store_true', help='Single question test')
    
    args = parser.parse_args()
    
    # Simple dataset check
    if not args.single_test and not os.path.exists(args.csv):
        print(f"Dataset not found: {args.csv}")
        return
    
    # Initialize agent
    agent = FinanceQAAgent(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        textbook_path=args.pdf
    )
    
    # Single question test
    if args.single_test:
        response = agent.answer_question(
            "What is Microsoft's diluted shares outstanding?",
            "Microsoft 10-K: Basic shares 7.4B, Employee stock options 45M shares"
        )
        print(f"Answer: {response['answer']}")
        return
    
    # Dataset path already validated above
    csv_path = args.csv
    
    # Run evaluation
    print(f"Running evaluation...")
    if args.subset:
        print(f"Testing {args.subset} questions")
    
    results = agent.evaluate_on_dataset(
        csv_path, 
        subset_size=args.subset,
        random_subset=args.random,
        max_workers=args.workers,
        random_seed=args.seed
    )
    
    save_results(agent, results, args.output)
    print(f"\n✅ Complete! Results saved to: {args.output}")


if __name__ == "__main__":
    main()
