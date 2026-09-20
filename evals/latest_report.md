# DocuSage eval report

- Mode: `offline`
- Items: 30 (25 answerable / 5 unanswerable)
- Groundedness proxy (answerable): **100.0%**
- Keyword hit rate (answerable): **100.0%**
- Answerable success: **100.0%**
- Abstention on unanswerable: **100.0%**
- Chat latency p50/p95: **0.0 / 0.01 ms**
- Summarize latency p50/p95: **0.0 / 0.0 ms**

## Notes

- Groundedness is token-overlap with context (proxy), not formal NLI.
- Offline mode stubs answers to validate the harness; live mode needs ai-service.
- Chat in the product uses stored summaries — same grounding idea as this eval.

Regenerate with `python3 evals/run_eval.py` (offline) or `python3 evals/run_eval.py --mode live`.
