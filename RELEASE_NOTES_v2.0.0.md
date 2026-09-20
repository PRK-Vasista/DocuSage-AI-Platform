# DocuSage v2.0.0 — GitHub release notes (paste into the release)

**Tag:** `v2.0.0`  
**Base:** builds on friend/local Docker release `v1.0.0`

## Summary

Quality and honesty release: docs match the real product (summary-grounded chat, not RAG), measurable AI latency, an offline eval harness, more reliable document processing with user retry, and CI on every push/PR.

## Highlights

- **Honest product docs** — README “is / is not”, Mermaid architecture and upload → Ready → chat sequence
- **Latency logs** — `duration_ms` on summarize and chat paths
- **Eval harness** — `evals/` golden Q&A (30 items), rule-based groundedness/abstention metrics; offline baseline in README
- **Processing reliability** — AI summarize retries + extractive fallback; clearer Failed errors; **Retry processing** (API + UI) without re-upload
- **CI** — GitHub Actions: backend pytest, AI-service pytest, eval unit tests, frontend ESM syntax check

## Intentionally not in this release

- Demo / verify / backup helper scripts
- Vector RAG, Redis queues, OpenTelemetry
- Public HTTPS / reverse proxy

## Upgrade notes

From `v1.0.0`:

```bash
git fetch --tags
git checkout v2.0.0
# or: git pull on main after the tag lands
cp .env.example .env   # only if you need new optional keys
docker compose up --build -d
```

Optional new env knobs (defaults are fine): `AI_SUMMARIZE_MAX_ATTEMPTS`, `AI_SUMMARIZE_RETRY_SECONDS`.

## Verify after upgrade

- Open http://localhost:3000 — register/login
- `curl http://localhost:8000/health`
- Upload a small file → Ready → summary + chat
- Force or find a Failed doc → **Retry processing** works
