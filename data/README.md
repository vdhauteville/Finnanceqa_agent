# Data Directory

This directory contains the data files used by the FinanceQA Agent.

## Contents

- **`Valuation.pdf`** - PDF textbook for RAG knowledge base
- **`financeqa_benchmark.csv`** - Full FinanceQA benchmark dataset (148 questions)

## Adding Your Own Data

### PDF Textbooks
Place additional PDF textbooks in this directory and reference them with the `--pdf` parameter:

```bash
python run.py --pdf data/your_textbook.pdf
```

### Datasets
Place your CSV datasets in this directory:

```bash
python run.py --csv data/your_dataset.csv
```

## Dataset Format

CSV files should contain these columns:
- `context` - Financial data or background information
- `question` - The question to answer
- `answer` - Expected answer for evaluation
- `question_type` (optional) - Question classification

Example:
```csv
context,question,answer,question_type
"Company ABC: Revenue $1B, COGS $600M","What is the gross profit margin?","40%","basic_tactical"
```
