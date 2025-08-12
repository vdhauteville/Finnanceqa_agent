# FinanceQA Agent

A comprehensive AI-powered agent for answering financial questions using Retrieval Augmented Generation (RAG) and chain-of-thought reasoning.

## Features

🧠 **Intelligent Question Classification**
- Automatically classifies questions as CONCEPTUAL, BASIC_TACTICAL, or ASSUMPTION_TACTICAL
- Adapts reasoning approach based on question type

📚 **Hybrid Knowledge Base**
- Hardcoded financial calculation rules for core concepts
- PDF textbook integration with intelligent chunking
- Table of contents parsing for better organization

⚡ **Optimized Performance** 
- Token-optimized prompts for cost efficiency
- Rate limiting and retry logic for API stability
- Parallel processing with configurable workers

🎯 **GAAP vs Non-GAAP Aware**
- Automatically identifies accounting standards
- Handles adjustments for non-GAAP measures
- Clear documentation of calculation assumptions

📊 **Comprehensive Evaluation**
- Detailed accuracy metrics by question type
- RAG utilization analysis
- Execution time tracking and optimization

## Installation

1. Clone the repository:
```bash
git clone <repository_url>
cd finance_qa_agent_final
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your OpenAI API key:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

4. (Optional) Place your PDF textbook in the `data/` directory as `data/Valuation.pdf`

## Quick Start

### Basic Usage

```python
from finance_qa_agent_final import FinanceQAAgent

# Initialize the agent
agent = FinanceQAAgent(
    openai_api_key="your-api-key",
    textbook_path="data/Valuation.pdf"  # Optional
)

# Answer a single question
response = agent.answer_question(
    question="What is the current ratio?",
    context="Company X has current assets of $500M and current liabilities of $300M"
)

print(f"Answer: {response['answer']}")
print(f"Classification: {response['question_type']}")
```

### Command Line Interface

Run a single question test:
```bash
python -m finance_qa_agent_final.main --single-test
```

Evaluate on a dataset:
```bash
python -m finance_qa_agent_final.main --csv your_dataset.csv --subset 100 --random
```

Test on full benchmark dataset:
```bash
python -m finance_qa_agent_final.main --subset 100 --random
```

Test on small subset:
```bash
python -m finance_qa_agent_final.main --subset 10 --random
```

Advanced usage with custom settings:
```bash
python -m finance_qa_agent_final.main \
    --subset 50 \
    --workers 2 \
    --delay 1.0 \
    --pdf data/Valuation.pdf \
    --output results.csv \
    --seed 123
```

## Configuration Options

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--csv` | `data/financeqa_benchmark.csv` | Path to CSV dataset |
| `--subset` | `None` | Number of questions to test (None = all) |
| `--random` | `False` | Use random subset vs first N questions |
| `--workers` | `2` | Number of parallel workers |
| `--output` | `results.csv` | Output file for results |
| `--seed` | `42` | Random seed for reproducible results |
| `--delay` | `0.5` | Delay between requests (seconds) |
| `--pdf` | `data/Valuation.pdf` | Path to PDF textbook |
| `--single-test` | `False` | Run single question test |

## Dataset Format

Your CSV dataset should contain the following columns:

```csv
context,question,answer,question_type
"Company ABC: Revenue $1B, COGS $600M","What is the gross profit margin?","40%","basic_tactical"
"","Explain the concept of WACC","Weighted Average Cost of Capital...","conceptual"
```

Required columns:
- `context`: Financial data or context (can be empty for conceptual questions)
- `question`: The financial question to answer
- `answer`: Expected answer for evaluation

Optional columns:
- `question_type`: Question classification (auto-detected if not provided)

## Knowledge Sources

### Hardcoded Financial Rules
The agent includes pre-configured rules for:
- Accounts Payable Days calculation
- Diluted shares computation
- EBITDA adjustments
- Variable lease assets estimation
- Working cash assumptions

### PDF Textbook Integration
- Automatic text extraction from PDF files
- Table of contents parsing for better organization
- Intelligent chunking (1500 characters per chunk)
- Section-based organization when possible

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PDF Textbook  │    │ Hardcoded Rules │    │  User Question  │
│                 │    │                 │    │                 │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────┬───────────┘                      │
                     │                                  │
              ┌──────▼──────┐                          │
              │   RAG System │                          │
              │             │                          │
              └──────┬──────┘                          │
                     │                                  │
                     └──────────┬───────────────────────┘
                                │
                         ┌──────▼──────┐
                         │   LLM Agent │
                         │   (GPT-4o)  │
                         └──────┬──────┘
                                │
                         ┌──────▼──────┐
                         │   Answer +  │
                         │ Evaluation  │
                         └─────────────┘
```

## Output

The agent generates comprehensive reports including:

### CSV Results
- Question-by-question analysis
- Confidence scores and reasoning
- RAG utilization tracking

### Detailed Report
- Overall accuracy metrics
- Breakdown by question type
- RAG utilization analysis
- Failed cases analysis
- Execution timing

### Console Output
```
==================================================
FINANCEQA BENCHMARK RESULTS
==================================================
Dataset: 100 questions
Overall Accuracy: 67.0% (67/100)
Paper Baseline: 54.1%
vs Baseline: +12.9%

By Question Type:
  Basic Tactical: 75.0% (30/40)
  Assumption Tactical: 60.0% (24/40)  
  Conceptual: 65.0% (13/20)

RAG Usage: 58/100 questions (58.0%)
```

## Performance Optimization

### Rate Limiting
- Automatic retry with exponential backoff
- Configurable request delays
- Reduced parallel workers to stay within API limits

### Token Optimization  
- Concise prompts (~40% token reduction)
- Efficient RAG chunk selection
- Optimized evaluation criteria

### Error Handling
- Graceful handling of rate limits
- Skip persistent failures rather than marking incorrect
- Detailed logging for debugging

## Troubleshooting

### Common Issues

**Rate Limit Errors (429)**
- Reduce `--workers` (try 1-2)
- Increase `--delay` (try 1.0-2.0)
- Check your OpenAI tier limits

**PDF Not Loading**
- Ensure PDF path is correct
- Check file permissions
- Verify PDF is text-extractable (not scanned images)

**Low Accuracy**
- Review failed cases in the detailed report
- Check if your dataset format matches expectations
- Verify question types are appropriate

**Memory Issues**
- Reduce subset size for testing
- Check available RAM for large PDFs
- Consider chunking very large datasets

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Citation

If you use this agent in your research, please cite:

```bibtex
@software{financeqa_agent,
  title={FinanceQA Agent: AI-Powered Financial Question Answering},
  author={FinanceQA Team},
  year={2024},
  url={https://github.com/your-repo/finance_qa_agent}
}
```
