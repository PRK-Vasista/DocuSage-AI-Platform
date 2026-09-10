# Platform Evolution

This is Copyright of DocuSage 2026 Owner Rohith Kumar Vasista P.

How DocuSage grew from early setup to the current product.  
Early delivery used **sprints**. From **v0.6** onward, work is delivered as **enhancements** (no more sprints).

---

## Timeline at a glance

| Phase | Version | Type | Outcome |
|-------|---------|------|---------|
| Setup / auth foundation | ~v0.1–v0.2 | Sprint | Project skeleton, Docker, JWT auth |
| Document management | **v0.3** | Sprint | Upload, list, download, trash, quota, modular code, Alembic |
| Processing pipeline | **v0.4** | Sprint | Extract text, background jobs, extractive summary, status UI |
| Local AI + chat | **v0.5** | Sprint | Isolated AI unit (Ollama), AI summary, per-document chat |
| Workspace UX | **v0.6** | Enhancement | Cursor-style UI, light/dark theme, summary+chat layout |
| Secrets & config | **v0.7** | Enhancement | `.env`, production fail-closed secrets, `LOG_LEVEL`, CORS |
| Reliability & ops | **v0.8** | Enhancement | Healthchecks, rate limits, AI warm-up UX, backup docs |
| Auth polish | **v0.9** | Enhancement | Change/reset password, friend/local Docker ready |
| First stable release | **v1.0.0** | Release | DocuSage ready to use and share locally |
| Post-v1 honesty & quality | **v1.1** | Enhancement | Docs match summary-grounded chat; eval, CI, retries (in progress) |

---

## Sprint era (feature building)

### Sprint ~1–2 — Foundations

- Multi-service Docker Compose layout  
- Backend and frontend containers  
- JWT-based registration and login  

### Sprint 3 — Document platform (`v0.3`)

- Secure document upload with validation  
- Per-user storage quota (1 GB) and per-file size limit (10 MB)  
- Soft delete (Trash) and permanent delete  
- Modular backend (`core`, `services`, `models`, …)  
- Modular frontend (`components`, `hooks`, `api`, …)  
- Fault-tolerant Alembic migrations on startup  
- Docker-based automated tests  

### Sprint 4 — Processing (`v0.4`)

- Text extraction for PDF / DOCX / plain text  
- Background processing with FastAPI `BackgroundTasks`  
- Status pipeline: `uploaded` → `processing` → `ready` / `failed`  
- Extractive summarization (no LLM yet)  
- Caps: 5 MB raw extraction (memory), 1 MB stored summary  
- Processing status in the UI with polling  

### Sprint 5 — AI assistant (`v0.5`)

- New **ai-service** container (isolated AI unit)  
- **Ollama** container for local LLM (`llama3.2:1b`) — no paid API key  
- Backend proxies summarize/chat; never talks to Ollama directly  
- AI summary preferred; extractive fallback if AI unit is down  
- Per-document chat with persisted history  
- Fixes: permanent delete with chat cleanup; Alembic revision ID length checks  

**Architectural milestone:** AI became a separate unit in the system.

```
Before v0.5:  Frontend → Backend → DB / files
After v0.5:   Frontend → Backend → AI Service → Ollama
                         Backend → DB / files
```

---

## Enhancement era (from v0.6)

Sprint-based delivery ended. Further work used enhancement versions through **`v1.0.0`**.

### Enhancement v0.6 — Workspace UI

- Cursor-like workspace instead of a single long dashboard page  
- **Left:** document list, add/remove, status, size, Active/Trash, quota  
- **Right top:** summary (collapsible) + download summary  
- **Right bottom:** ongoing chat  
- Top bar: brand, light/dark toggle, profile, logout  
- Theme preference stored in the browser  

### Enhancement v0.7 — Secrets, config, logging

- Root `.env.example` + Compose `env_file` / interpolation  
- `APP_ENV`, `LOG_LEVEL`, `CORS_ORIGINS`  
- Production refuses weak `SECRET_KEY` / sample DB password  
- Module-level forced DEBUG logging removed  

### Enhancement v0.8 — Reliability & ops

- Backend `/health`; AI health reports model availability  
- Compose `service_healthy` dependency chain  
- In-process rate limits (auth, upload, chat)  
- Workspace AI status banner; chat retry  
- Backup/restore documentation  

### Enhancement v0.9 — Minimal auth polish

- Change password (authenticated)  
- Forgot/reset password with hashed one-time tokens  
- Optional SMTP via stdlib only (no email SDKs)  
- Mandatory email verification deferred (post-v1)  

### Release v1.0.0

- First stable release of DocuSage  
- Friend/local Docker target (no public TLS reverse proxy in this release)  
- Version tags and docs marked current at `v1.0.0`  

### Enhancement v1.1 — Honesty, metrics, reliability (ongoing)

Shipped as small Improvements (each committed separately):

1. Truthful docs + Mermaid architecture/sequence (summary-grounded chat, not RAG)  
2. Latency logging on summarize/chat  
3. Eval harness + baseline metrics  
4. Processing retries + clearer Failed status  
5. Expanded tests + GitHub Actions CI  
6. Demo / verify / backup scripts  

**Not in v1.1:** vector RAG, Redis queues, OpenTelemetry.

---

## Versioning convention (development practice)

Commit style (general):

```text
<type> | <version> | <short message>
```

Examples of types: `Feature`, `Enhancement`, `Bug`, `Release`.

---

## Related docs

- [Architecture](./architecture.md)  
- [Services](./services.md)  
- [Development Guide](./development-guide.md)  
- [Production checklist](../PRODUCTION.md)  
- [Changelog](../CHANGELOG.md)  
