# DocuSage AI Platform

**Current version:** `v0.6` (enhancement phase)

DocuSage is a full-stack web application for secure document upload, management, and AI-powered analysis. It runs as a multi-service Docker Compose stack with a modular FastAPI backend, React frontend, and an **isolated local AI unit** (no paid API keys).

---

## What is DocuSage?

DocuSage lets users:

1. **Authenticate** via JWT-based registration and login
2. **Upload** text-based documents (PDF, TXT, DOCX, MD, and similar)
3. **Manage** documents with list, download, soft-delete, and permanent delete
4. **Process & summarize** documents (AI summary via local Ollama; extractive fallback)
5. **Chat with documents** using the isolated AI unit
6. **Workspace UI** with document rail, summary, chat, and light/dark theme *(v0.6 enhancements)*

---

## Architecture

| Component | Responsibility | Technology |
|-----------|----------------|------------|
| **Frontend** | Workspace UI (doc rail + summary/chat), auth, light/dark theme | React, JavaScript, CSS |
| **Backend** | API, auth, files, chat proxy (no direct LLM calls) | FastAPI, Python 3.10 |
| **AI Service** | Isolated summarize + chat unit | FastAPI, httpx |
| **Ollama** | Local LLM runtime (no API key) | `llama3.2:1b` (CPU-friendly) |
| **Database** | Users, documents, chat history, migrations | PostgreSQL 15, SQLAlchemy, Alembic |
| **File storage** | Uploaded document binaries | Docker volume (`user_uploads/`) |

### Services (Docker Compose)

| Service | Container name | Port |
|---------|----------------|------|
| Database | `docu-sage-db` | `5432` |
| Ollama | `docu-sage-ollama` | `11434` |
| AI Service | `docu-sage-ai` | `8100` |
| Backend | `docu-sage-backend` | `8000` |
| Frontend | `docu-sage-frontend` | `3000` |

---

## Current Status

### Enhancement phase — In progress (`v0.6+`)

Post-feature work uses **minor versions** (`v0.6`, `v0.7`, `v0.8`, …) until the first production release. No more sprints.

- Cursor-style workspace: left document rail, right summary + chat *(v0.6)*
- Light / dark theme with persistence
- Profile menu + logout in the top bar
- Collapsible summary + download summary as `.txt`
- Later enhancement batches continue as `v0.7`, `v0.8`, … as needed

### Feature baseline — Complete (`v0.5`)

- Isolated **AI unit**: `ai-service` + `ollama` containers (backend never talks to Ollama directly)
- Local LLM via Ollama (`llama3.2:1b`) — **no paid API key**
- AI summarization in the processing pipeline (extractive fallback if AI unit is down)
- Per-document chat API: `GET/POST /api/v1/chat/{document_id}`
- Chat history table + Alembic migration `0003_chat_messages`
- Docker tests with mocked AI (no live model calls in CI)

### Earlier milestones

| Version | Focus |
|---------|-------|
| `v0.4` | Text extraction, background processing, extractive summary, status UI |
| `v0.3` | Auth, upload, trash/permanent delete, quota, modular app, Alembic, Docker tests |

### Roadmap

| Version | Focus |
|---------|-------|
| `v0.6`, `v0.7`, `v0.8`, … | Enhancement batches (minor bumps) |
| `v1.0.0` | Production-ready first public release |

---

## Project Structure

```
DocuSage-AI-Platform/
├── backend/
│   ├── app/
│   │   ├── core/           # Config, exceptions, exception handlers
│   │   ├── dependencies/   # FastAPI dependencies (auth)
│   │   ├── models/         # SQLAlchemy ORM models
│   │   ├── schemas/        # Pydantic request/response schemas
│   │   ├── services/       # Business logic + AI client (proxy only)
│   │   └── routers/        # API route handlers
│   ├── alembic/            # Database migrations
│   ├── tests/              # Automated tests
│   ├── Dockerfile
│   └── requirements.txt
├── ai-service/             # Isolated AI unit (summarize + chat)
│   ├── app/
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/     # TopBar, Workspace, AuthForm, shared UI
│   │   ├── hooks/          # Custom hooks (useAuth)
│   │   ├── api/            # API service layer
│   │   ├── config/         # Frontend configuration
│   │   └── utils/          # Formatters and helpers
│   └── Dockerfile
├── docker-compose.yaml
└── README.md
```

---

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Git

### 1. Clone the repository

```bash
git clone https://github.com/PRK-Vasista/DocuSage-AI-Platform.git
cd DocuSage-AI-Platform
```

### 2. Build and start all services

```bash
docker compose up --build -d
```

The first run may take several minutes while images are built and Ollama downloads `llama3.2:1b` (one-time model pull).

### 3. Verify services are running

```bash
docker compose ps
```

Services `db`, `ollama`, `ai-service`, `backend`, and `frontend` should be **running**. The database must be **healthy** before the backend starts.

If the first AI summary is slow or fails once, wait for the model pull to finish:

```bash
docker compose logs -f ai-service
docker compose exec ollama ollama list
```

### 4. Access the application

| URL | Purpose |
|-----|---------|
| http://localhost:3000 | Frontend UI |
| http://localhost:8000/docs | Backend API documentation (Swagger) |
| http://localhost:8100/docs | AI service API documentation |
| http://localhost:8000 | Backend health check |
| http://localhost:8100/api/v1/ai/health | AI unit health |

---

## Manual Testing

There is **no default app login**. Register a new user on first use.

### App login (UI)

1. Open http://localhost:3000
2. Click **Register** and create an account (e.g. `user@test.com` / `password123`)
3. Log in — you should land in the **workspace** layout
4. Use the top-right **Dark/Light** toggle and confirm theme persists after refresh
5. Open the profile menu → **Log out**

### Workspace (document rail + summary/chat)

1. In the **left panel**, click **Add file** and upload a `.txt` / `.md` / `.pdf` / `.docx`
2. Watch the status badge: `Uploaded` → `Processing` → `Ready`
3. Select the document — **right panel** shows **Summary** on top and **Chat** below
4. Use **Collapse** on the summary if it is long; use **Download summary** to save a `.txt`
5. Chat about the document in the lower right panel
6. Use **Active / Trash** in the left rail; **Remove** soft-deletes; trash supports permanent delete
7. Storage quota appears at the bottom of the left rail
8. Try uploading an unsupported file (e.g. `.exe`) — should be rejected

### Database credentials (for local DB tools only)

| Setting | Value |
|---------|-------|
| Host | `localhost` |
| Port | `5432` |
| Database | `docu_sage_db` |
| User | `user` |
| Password | `password` |

These are for PostgreSQL access only — **not** the web app login.

---

## Automated Tests (Docker)

Run backend tests:

```bash
docker compose build backend
docker compose run --rm backend pytest -v
```

Run AI service tests (Ollama mocked):

```bash
docker compose build ai-service
docker compose run --rm ai-service pytest -v
```

Expected: all tests pass.

---

## Viewing Logs

Use **separate terminals** to follow logs continuously:

```bash
# Terminal 1 — Backend
docker compose logs -f --timestamps backend

# Terminal 2 — AI service
docker compose logs -f --timestamps ai-service

# Terminal 3 — Ollama
docker compose logs -f --timestamps ollama

# Terminal 4 — Frontend
docker compose logs -f --timestamps frontend

# Terminal 5 — Database (optional)
docker compose logs -f --timestamps db
```

Press `Ctrl+C` to stop watching. Containers keep running.

---

## Database Migrations (Alembic)

Migrations run automatically when the backend starts. Configuration is controlled via environment variables in `docker-compose.yaml`:

| Variable | Default | Purpose |
|----------|---------|---------|
| `ENABLE_ALEMBIC_MIGRATIONS` | `true` | Run Alembic on startup |
| `ENABLE_CREATE_ALL_FALLBACK` | `true` | Fallback to `create_all()` if migrations fail (dev safety net) |
| `DB_MIGRATION_MAX_RETRIES` | `5` | Retry count when DB is not ready |
| `DB_MIGRATION_RETRY_SECONDS` | `2` | Delay between retries |

### Check current migration revision

```bash
docker compose exec backend alembic current
```

### Manual migration (if needed)

```bash
docker compose exec backend alembic upgrade head
```

---

## API Endpoints (Summary)

### Auth — `/api/v1/auth`

| Method | Path | Description |
|--------|------|-------------|
| POST | `/register` | Register and receive JWT |
| POST | `/login` | Login and receive JWT |
| GET | `/me` | Get current user (protected) |

### Files — `/api/v1/files`

| Method | Path | Description |
|--------|------|-------------|
| POST | `/upload` | Upload a document; queues background processing (protected) |
| GET | `/` | List documents (protected) |
| GET | `/{id}` | Get document metadata (protected) |
| GET | `/{id}/summary` | Get document summary and processing status (protected) |
| GET | `/{id}/download` | Download document (protected) |
| DELETE | `/{id}` | Soft delete — move to trash (protected) |
| DELETE | `/{id}/permanent` | Permanent delete — trash only (protected) |

### Chat — `/api/v1/chat`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/{document_id}` | Get chat history for a document (protected) |
| POST | `/{document_id}` | Ask a question about a ready document (protected) |

### AI Service (internal unit) — `/api/v1/ai`

Called by the backend only (not by the browser):

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | AI unit + Ollama health |
| POST | `/summarize` | Summarize document text |
| POST | `/chat` | Document-grounded chat completion |

Full interactive docs: http://localhost:8000/docs and http://localhost:8100/docs

---

## Upload Limits

| Rule | Limit |
|------|-------|
| Max file size | 10 MB per upload |
| Max raw extracted text (processing) | 5 MB |
| Max stored summary in database | 1 MB (summarized, not raw extraction) |
| Max storage per user | 1 GB total |
| Allowed types | PDF, TXT, DOCX, MD, CSV, JSON, XML, HTML, RTF, LOG, and other text-based files |

---

## Teardown and Reset

### Stop services (keep data)

```bash
docker compose down
```

### Full reset — delete all data

```bash
docker compose down --volumes
```

**Warning:** This permanently deletes all users, document metadata, and uploaded files.

### Start fresh after reset

```bash
docker compose up --build -d
```

Register a new user again after a full reset.

---

## Commit Message Convention

```
<type> | <version> | <short message>
```

Examples:

```
Feature | v0.5 | Isolated AI unit with Ollama summarization and chat
Enhancement | v0.6 | Enhancement of UI with Light/dark theme
Bug | v0.6.1 | Fix permanent delete when chat messages exist
Release | v1.0.0 | Production-ready first public release
```

---

## Development Notes

- Backend hot-reloads on code changes (`./backend` is mounted into the container)
- Frontend hot-reloads on `./frontend/src` changes
- Secrets and runtime data are excluded via `.gitignore` (`.env`, `user_uploads/`, `.venv/`, etc.)
- Do **not** commit `.env` files or uploaded documents to Git

---

## License

Private project — all rights reserved.
