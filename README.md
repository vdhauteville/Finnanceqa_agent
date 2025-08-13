# FinanceQA Agent

A comprehensive AI-powered agent for answering financial questions using Retrieval Augmented Generation (RAG) and chain-of-thought reasoning.

## Installation

1. Clone the repository and navigate to it:
```bash
git clone <repository_url>
cd claude_agent
```

2. Activate the pre-configured virtual environment:
```bash
source myenv/bin/activate  # On macOS/Linux
# OR
myenv\Scripts\activate     # On Windows
```

3. Install dependencies:
```bash
pip install -r finance_qa_agent_final/requirements.txt
```

4. Set up your OpenAI API key:
```bash
export OPENAI_API_KEY="your-api-key-here"
```
Or create a `.env` file in the project root:
```
OPENAI_API_KEY=your-api-key-here
```

5. Navigate to the main agent directory:
```bash
cd finance_qa_agent_final
```

Note: The PDF textbook (`Valuation.pdf`) is already included in the `data/` directory.

## Quick Start

### Basic Usage

```python
# From within the finance_qa_agent_final directory
from agent import FinanceQAAgent

# Initialize the agent
agent = FinanceQAAgent(
    openai_api_key="your-api-key",
    textbook_path="data/Valuation.pdf"  # PDF is included
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

First, make sure you're in the `finance_qa_agent_final` directory:
```bash
cd finance_qa_agent_final  # If not already there
```

Run a single question test:
```bash
python main.py --single-test
```

Evaluate on a dataset:
```bash
python main.py --csv your_dataset.csv --subset 100 --random
```

Test on full benchmark dataset:
```bash
python main.py --subset 100 --random
```

Test on small subset:
```bash
python main.py --subset 10 --random
```

Custom settings:
```bash
python main.py --subset 50 --workers 1 --output my_results.csv
```

Conservative rate limiting (avoid 429 errors):
```bash
python main.py --subset 10 --workers 1 --delay 1.0
```

Use GPT-4o-mini for higher rate limits:
```bash
python main.py --subset 10 --model gpt-4o-mini
```

## Configuration Options

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--csv` | `data/financeqa_benchmark.csv` | Path to CSV dataset |
| `--subset` | `None` | Number of questions to test (None = all) |
| `--random` | `False` | Use random subset vs first N questions |
| `--workers` | `1` | Number of parallel workers (conservative for rate limiting) |
| `--output` | `results.csv` | Output file for results |
| `--seed` | `42` | Random seed for reproducible results |

| `--pdf` | `data/Valuation.pdf` | Path to PDF textbook |
| `--delay` | `0.5` | Delay between requests in seconds |
| `--model` | `gpt-4o` | OpenAI model to use (gpt-4o, gpt-4o-mini, etc.) |
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
