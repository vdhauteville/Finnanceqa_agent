## Agent Card
This agent answers financial questions from the FinanceQA benchmark using a mix of hardcoded accounting rules, a RAG setup with the *Valuation: Measuring and Managing the Value of Companies* PDF, and a bit of question-type smarts.  
It first figures out whether the question needs assumptions (e.g., missing data, conceptual asks), then either answers directly or generates those assumptions before calculating. It also warns itself if it’s about to compute a non-GAAP measure.

**Main features:**
- **Question classification** – Is it basic, assumption-based, or conceptual?  
- **RAG** – Pulls context from the *Valuation* textbook.  
- **GAAP/Non-GAAP awareness** – Light checks before answering.  
- **Token-conscious prompts** – Keeps things short for speed + cost.  
- **Parallel processing** – Runs multiple questions at once (without tripping rate limits).  

---

## Design Approach
From the paper, one big pain point was conceptual questions: models weren’t realizing they needed to make assumptions, and they sometimes ignored accounting rules.  
My approach was to split the problem into two steps:
1. **Classify the question** – Detect if it needs assumptions or if it’s straightforward.  
2. **Answer it** – If assumptions are needed, pull relevant info from the textbook and create them before answering.

The textbook cited in the paper turned out to be findable online (thanks, Google), so I pulled that into the RAG component. My design mainly focuses on improving assumption-heavy questions.

### Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PDF Textbook  │    │ Hardcoded Rules │    │  User Question  │
│   (Valuation)   │    │ (Financial Calc)│    │                 │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────┬───────────┘                      │
                     │                                  │
              ┌──────▼──────┐                          │
              │ RAG System  │                          │
              │ - Chunking  │                          │
              │ - Retrieval │                          │
              └──────┬──────┘                          │
                     │                                  │
                     └──────────┬───────────────────────┘
                                │
                         ┌──────▼──────┐
                         │ Question    │
                         │ Classifier  │
                         └──────┬──────┘
                                │
                         ┌──────▼──────┐
                         │   LLM Core  │
                         │   (GPT-4o)  │
                         │ + Chain of  │
                         │   Thought   │
                         └──────┬──────┘
                                │
                         ┌──────▼──────┐
                         │ Numerical   │
                         │ Evaluator   │
                         └──────┬──────┘
                                │
                         ┌──────▼──────┐
                         │   Final     │
                         │   Answer    │
                         └─────────────┘
```

---

## Key Trade-offs and Decisions
- **One-step vs. two-step** – I went with a single LLM call for both classification and answering, mainly because it was easier to debug and keep the flow consistent.  
- **Prompt length** – Kept prompts short to cut token use. That let me run more in parallel and avoid hitting API rate limits.  
- **Subset evaluation** – During dev I tested on a 50-question subset out of 148. This ran in ~5–10 minutes depending on token size.  
- **GAAP handling** – Agent warns itself if it might be outputting a non-GAAP measure.

---

## Evaluation on Benchmark
- Baseline from the paper (non-agentic OpenAI): **54.1%**  
- Agent run (example config from README):  
  - **Overall**: 67% (+12.9% vs. baseline)  
  - **Basic tactical**: 75%  
  - **Assumption tactical**: 60%  
  - **Conceptual**: 65%  
- RAG was used in ~58% of the evaluated questions.  
- Most gains came from assumption tactical and conceptual types — exactly the target.

---

## Suggestions for Future Improvements
- Add more RAG sources beyond *Valuation* to improve coverage.  
- Better prompts nudging the model to stick to accounting conventions and proper formatting.  
- More systematic testing with different RAG and prompt configurations.  
- With stronger finance knowledge, I’d add:
  - More meaningful verification rules  
  - Post-processing checks for compliance with GAAP and other standards  
  - Targeted improvements for conceptual questions.

