# DocuSage AI Platform

**Current version:** `v0.4` (Sprint 4 complete)

DocuSage is a full-stack web application for secure document upload, management, and (in upcoming sprints) AI-powered analysis. It runs as a multi-service Docker Compose stack with a modular FastAPI backend and React frontend.

---

## What is DocuSage?

DocuSage lets users:

1. **Authenticate** via JWT-based registration and login
2. **Upload** text-based documents (PDF, TXT, DOCX, MD, and similar)
3. **Manage** documents with list, download, soft-delete, and permanent delete
4. **Process & summarize** documents with background extraction and extractive summarization *(Sprint 4)*
5. **Chat with documents** using AI *(planned — Sprint 5+)*

---

## Architecture

| Component | Responsibility | Technology |
|-----------|----------------|------------|
| **Frontend** | UI, auth state, document dashboard | React, JavaScript, CSS |
| **Backend** | API, business logic, file handling, JWT security | FastAPI, Python 3.10 |
| **Database** | Users, document metadata, migration history | PostgreSQL 15, SQLAlchemy (async), Alembic |
| **File storage** | Uploaded document binaries | Docker volume (`user_uploads/`) |

### Services (Docker Compose)

| Service | Container name | Port |
|---------|----------------|------|
| Database | `docu-sage-db` | `5432` |
| Backend | `docu-sage-backend` | `8000` |
| Frontend | `docu-sage-frontend` | `3000` |

---

## Current Status

### Sprint 4 — Complete (`v0.4`)

- Background text extraction after upload (PDF, DOCX, plain text) via FastAPI `BackgroundTasks`
- Extractive summarization of the full document (stdlib — no LLM dependency)
- Processing pipeline: `uploaded` → `processing` → `ready` / `failed`
- Document summary stored in DB (max 1 MB); raw extraction capped at 5 MB during processing
- `GET /files/{id}/summary` endpoint
- Dashboard status badges, auto-polling, and **View Summary** panel
- Alembic migration `0002_add_document_processing_fields`
- New dependencies: `pypdf`, `python-docx` (user-approved)

### Sprint 3 — Complete (`v0.3`)

- User registration, login, JWT auth, and session persistence
- Document upload with validation (10 MB per file, 1 GB per user)
- Allowed types: PDF, TXT, DOCX, MD, and other text-based files
- Document list, metadata, and download
- Soft delete (trash) → permanent delete flow
- Storage quota display in the dashboard
- Modular backend (`core/`, `services/`, `models/`, `dependencies/`)
- Modular frontend (`components/`, `hooks/`, `api/`, `config/`)
- Fault-tolerant Alembic migrations on startup
- Docker-based automated tests (`pytest`)

### Upcoming

| Sprint | Version | Focus |
|--------|---------|-------|
| Sprint 5 | `v0.5` | AI-powered summarization and chat with documents |
| Release | `v1.0.0` | Production-ready first public version |

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
│   │   ├── services/       # Business logic layer
│   │   └── routers/        # API route handlers
│   ├── alembic/            # Database migrations
│   ├── tests/              # Automated tests
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/     # React UI components
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

The first run may take a few minutes while images are built.

### 3. Verify services are running

```bash
docker compose ps
```

All three services (`db`, `backend`, `frontend`) should be **running**. The database must be **healthy** before the backend starts.

### 4. Access the application

| URL | Purpose |
|-----|---------|
| http://localhost:3000 | Frontend UI |
| http://localhost:8000/docs | Backend API documentation (Swagger) |
| http://localhost:8000 | Backend health check |

---

## Manual Testing

There is **no default app login**. Register a new user on first use.

### App login (UI)

1. Open http://localhost:3000
2. Click **Register** and create an account (e.g. `user@test.com` / `password123`)
3. Log in and confirm the dashboard loads
4. Refresh the page — you should remain logged in

### Document management

1. Upload a `.txt` or `.md` file — it should appear under **My Documents**
2. Check **Storage Usage** updates
3. Watch the **Status** badge move: `Uploaded` → `Processing` → `Ready` (polls every 3 seconds)
4. Click **View Summary** when status is `Ready` — summarized document text should appear
5. Click **Download** — file should download
6. Click **Delete** — file moves to **Trash**
7. Open **Trash** tab → **Delete Permanently**
8. Try uploading an unsupported file (e.g. `.exe`) — should be rejected
9. Upload a `.pdf` or `.docx` file — confirm extraction and summary work the same way

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

Run all backend tests inside the backend container:

```bash
docker compose build backend
docker compose run --rm backend pytest -v
```

Expected: all tests pass.

---

## Viewing Logs

Use **separate terminals** to follow logs continuously:

```bash
# Terminal 1 — Backend
docker compose logs -f --timestamps backend

# Terminal 2 — Frontend
docker compose logs -f --timestamps frontend

# Terminal 3 — Database (optional)
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

Full interactive docs: http://localhost:8000/docs

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

All commits follow this format:

```
Sprint-<N> | v0.<N>[.<patch>] | <short one-line description>
```

| Type | Example |
|------|---------|
| Sprint feature | `Sprint-3 \| v0.3 \| Document upload, trash flow, Alembic migrations, modular frontend, and Docker tests` |
| Sprint bug fix | `Sprint-3 \| v0.3.1 \| Fix upload route prefix mismatch` |
| Final release (future) | `Sprint-8 \| v1.0.0 \| Production release` |

---

## Development Notes

- Backend hot-reloads on code changes (`./backend` is mounted into the container)
- Frontend hot-reloads on `./frontend/src` changes
- Secrets and runtime data are excluded via `.gitignore` (`.env`, `user_uploads/`, `.venv/`, etc.)
- Do **not** commit `.env` files or uploaded documents to Git

---

## License

Private project — all rights reserved.
