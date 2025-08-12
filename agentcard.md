# FinanceQA Agent Card

## Agent Information

**Name:** FinanceQA Agent
**Version:** 1.0.0
**Type:** Financial Question Answering System
**Domain:** Finance & Accounting

## Overview
**Purpose:** AI agent that replicates junior investment analyst work on the FinanceQA benchmark  
**Target:** beating 39.2% GPT-4o baseline  

## Capabilities
Performs financial analysis tasks from hedge funds, PE firms, and investment banks:
- **Financial calculations** from 10-K filings (diluted shares, EBITDA, working capital)
- **Assumption-based estimation** when data is incomplete (variable lease assets, working cash)
- **Accounting compliance** (ASC 842 lease standards, GAAP principles)

## Architecture
- **Question Classifier:** Rules-based categorization (Conceptual/Basic Tactical/Assumption Tactical)
- **Financial Rules Engine:** Hardcoded calculation methodologies + common error patterns
- **RAG System:** PDF textbook integration with semantic search
- **GPT-4o Core:** Specialized financial prompting with type-specific templates
- **Exact Match Evaluator:** Binary scoring with rounding tolerance

## Key Design Choices
**Hardcoded rules over pure RAG** - More reliable for core calculations  
**Question-type specialization** - Higher accuracy than generic prompts  
**Exact match evaluation** - Meets financial precision requirements  
**Parallel processing** - Faster evaluation with rate limiting  


## Key Improvements
- **Financial domain expertise:** Addresses calculation errors from FinanceQA paper
- **ASC 842 compliance:** Operating lease adjustments in EBITDA/Enterprise Value
- **Assumption guidance:** Explicit rules for incomplete data scenarios
- **Robust error handling:** OpenAI-specific retry logic with exponential backoff

## Usage
```bash
# Basic run
python financeqa_agent.py --csv dataset.csv

# With textbook RAG
python financeqa_agent.py --subset 50 --pdf Valuation.pdf --random



## Capabilities

- [ ] Question Classification
- [ ] Chain-of-Thought Reasoning  
- [ ] RAG Integration
- [ ] GAAP/Non-GAAP Handling
- [ ] PDF Knowledge Extraction

## Performance Metrics

| Metric | Value | Baseline |
|--------|-------|----------|
| Overall Accuracy | TBD | 54.1% |
| Basic Tactical | TBD | TBD |
| Assumption Tactical | TBD | TBD |
| Conceptual | TBD | TBD |

## Knowledge Sources

- [ ] Hardcoded Financial Rules
- [ ] PDF Textbook Content
- [ ] RAG Retrieval System

## Limitations

[Add known limitations here]

## Usage Guidelines

[Add usage recommendations here]

## Evaluation

[Add evaluation details here]

## Updates

[Add version history here]
