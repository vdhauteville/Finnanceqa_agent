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
    parser.add_argument('--workers', type=int, default=2, help='Number of parallel workers (default: 3, reduced for rate limiting)')
    parser.add_argument('--output', default='results.csv', help='Output file for results')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for reproducible subsets (default: 42)')
    parser.add_argument('--delay', type=float, default=0.5, help='Delay between requests in seconds (default: 0.5)')
    parser.add_argument('--pdf', default='data/Valuation.pdf', help='Path to PDF textbook for RAG (default: data/Valuation.pdf)')
    parser.add_argument('--single-test', action='store_true', help='Just run single question test')
    
    args = parser.parse_args()
    
    # Check if dataset exists (unless doing single test)
    if not args.single_test:
        csv_path = args.csv
        if not os.path.exists(csv_path):
            print(f"\nError: Dataset not found at {csv_path}")
            print("Please ensure your dataset file exists or specify a different path with --csv")
            return
    
    # Initialize agent
    agent = FinanceQAAgent(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        textbook_path=args.pdf
    )
    
    # Single question test
    if args.single_test:
        question = "What is Microsoft's diluted shares outstanding?"
        context = "Microsoft 10-K: Basic shares 7.4B, Employee stock options 45M shares"
        
        response = agent.answer_question(question, context)
        print("Single Question Test:")
        print(f"Q: {question}")
        print(f"A: {response['answer']}")
        print(f"Type: {response['question_type']}")
        return
    
    # Dataset path already validated above
    csv_path = args.csv
    
    # Run evaluation
    print(f"\n{'='*50}")
    print("BENCHMARK EVALUATION")
    print(f"{'='*50}")
    
    if args.subset:
        print(f"Running with subset: {args.subset} questions ({'random' if args.random else 'sequential'})")
    else:
        print("Running with full dataset")
    
    print(f"Parallel workers: {args.workers}")
    
    # Show knowledge source info
    total_chunks = len(agent.rag.knowledge_chunks)
    hardcoded_chunks = len([c for c in agent.rag.knowledge_chunks if c.get('source') != 'pdf_valuation'])
    pdf_chunks = total_chunks - hardcoded_chunks
    
    print(f"Knowledge Sources:")
    print(f"  • Hardcoded rules: {hardcoded_chunks} chunks")
    if pdf_chunks > 0:
        print(f"  • PDF textbook: {pdf_chunks} chunks from {args.pdf}")
    else:
        print(f"  • PDF textbook: Not found at {args.pdf}")
    print(f"  • Total: {total_chunks} knowledge chunks")
    
    results = agent.evaluate_on_dataset(
        csv_path, 
        subset_size=args.subset,
        random_subset=args.random,
        max_workers=args.workers,
        random_seed=args.seed,
        delay_between_requests=args.delay
    )
    
    save_results(agent, results, args.output)
    print(f"\n✅ Complete! Results saved to: {args.output}")


if __name__ == "__main__":
    main()
