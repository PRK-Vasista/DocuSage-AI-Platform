# Developer Documentation

This is Copyright of DocuSage 2026 Owner Rohith Kumar Vasista P.

Technical documentation for contributors and maintainers of **DocuSage AI Platform**.

If you are an end user looking for how to use the app, see the root **[README.md](../README.md)**.

---

## Contents

| Document | Description |
|----------|-------------|
| [Architecture](./architecture.md) | System overview, Mermaid flows, design principles |
| [Services](./services.md) | What each Docker service does and how they talk |
| [Evolution](./evolution.md) | Platform history through sprints and enhancements |
| [Development Guide](./development-guide.md) | Local setup, tests, CI, migrations, APIs |

---

## Quick map of the repository

```
DocuSage-AI-Platform/
├── frontend/                 # React workspace UI
├── backend/                  # FastAPI API + auth + files + chat proxy
├── ai-service/               # Isolated AI unit (summarize + chat)
├── evals/                    # Offline golden Q&A + metric helpers
├── .github/workflows/        # CI (pytest + light syntax checks)
├── docker-compose.yaml       # Orchestrates all services
├── README.md                 # End-user documentation
├── PRODUCTION.md             # Friend/local Docker deploy checklist
└── developer-documentation/  # This folder
```

**Current product version:** `v2.0.0`
