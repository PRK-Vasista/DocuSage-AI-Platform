# Developer Documentation

This is Copyright of DocuSage 2026 Owner Rohith Kumar Vasista P.

Technical documentation for contributors and maintainers of **DocuSage AI Platform**.

If you are an end user looking for how to use the app, see the root **[README.md](../README.md)**.

---

## Contents

| Document | Description |
|----------|-------------|
| [Architecture](./architecture.md) | System overview, data flow, and design principles |
| [Services](./services.md) | What each Docker service does and how they talk |
| [Evolution](./evolution.md) | Platform history through sprints and enhancements |
| [Development Guide](./development-guide.md) | Local setup, tests, logs, migrations, APIs |

---

## Quick map of the repository

```
DocuSage-AI-Platform/
├── frontend/                 # React workspace UI
├── backend/                  # FastAPI API + auth + files + chat proxy
├── ai-service/               # Isolated AI unit (summarize + chat)
├── docker-compose.yaml       # Orchestrates all services
├── README.md                 # End-user documentation
└── developer-documentation/  # This folder
```

**Current product version:** `v1.0.0` (first stable friend/local Docker release)
