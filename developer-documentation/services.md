# Services

This is Copyright of DocuSage 2026 Owner Rohith Kumar Vasista P.

All services are defined in `docker-compose.yaml` and share one Docker network.

---

## Service summary

| Service | Container | Port | Role |
|---------|-----------|------|------|
| `frontend` | `docu-sage-frontend` | `3000` | React UI (workspace) |
| `backend` | `docu-sage-backend` | `8000` | FastAPI API gateway + business logic |
| `ai-service` | `docu-sage-ai` | `8100` | Summarize + chat HTTP unit |
| `ollama` | `docu-sage-ollama` | `11434` | Local LLM runtime |
| `db` | `docu-sage-db` | `5432` | PostgreSQL 15 |

---

## 1. Frontend (`frontend/`)

**Purpose:** End-user interface.

**Responsibilities:**
- Registration and login screens  
- Cursor-style workspace: left document rail, right summary + chat  
- Light / dark theme, profile menu, logout  
- Calls backend REST APIs only (never talks to AI service or Ollama)  

**Tech:** React, JavaScript, CSS  

**Useful URL:** http://localhost:3000  

---

## 2. Backend (`backend/`)

**Purpose:** Application API and orchestration.

**Responsibilities:**
- JWT auth (register, login, `/me`)  
- File upload validation, storage, quota  
- Document list, download, soft delete, permanent delete  
- Background document processing (extract text, request summary)  
- Chat API that proxies inference to `ai-service`  
- Alembic migrations on startup  
- Does **not** call Ollama directly  

**Tech:** FastAPI, SQLAlchemy (async), Alembic, pypdf, python-docx, httpx  

**Layout (high level):**

```
backend/app/
├── core/           # config, exceptions, handlers
├── dependencies/   # auth dependencies
├── models/         # ORM
├── schemas/        # request/response models
├── services/       # business logic + AI client
└── routers/        # auth, files, chat
```

**Useful URLs:**
- API docs: http://localhost:8000/docs  
- Health-style root: http://localhost:8000  

---

## 3. AI Service (`ai-service/`)

**Purpose:** Isolated AI unit for summarization and document-grounded chat.

**Responsibilities:**
- `POST /api/v1/ai/summarize` — build an overall-document summary  
- `POST /api/v1/ai/chat` — answer questions using provided document context  
- `GET /api/v1/ai/health` — service + Ollama reachability  
- Talks **only** to Ollama over HTTP  

**Tech:** FastAPI, httpx, pydantic-settings  

**Useful URL:** http://localhost:8100/docs  

---

## 4. Ollama (`ollama` image)

**Purpose:** Local model runtime (no cloud API key).

**Responsibilities:**
- Host LLM weights and serve generation/chat APIs  
- Default model in compose: `llama3.2:1b` (CPU-friendly for ~16 GB RAM laptops)  

**Useful checks:**

```bash
docker compose exec ollama ollama list
docker compose logs -f ollama
```

---

## 5. Database (`db` / PostgreSQL)

**Purpose:** Durable application data.

**Responsibilities:**
- Users and password hashes  
- Document metadata and summaries  
- Chat message history  
- Alembic version tracking  

**Default local credentials (dev only — override via `.env`):**

| Setting | Value |
|---------|-------|
| Database | from `POSTGRES_DB` (default `docu_sage_db`) |
| User | from `POSTGRES_USER` (default `user`) |
| Password | from `POSTGRES_PASSWORD` (default `password`) |
| Port | `5432` |

These are **not** the web app login. For production, set strong values and `APP_ENV=production`.

Startup order uses Compose healthchecks: **db** → **ollama** → **ai-service** → **backend** → **frontend**.

---

## How services depend on each other

Startup order (conceptually):

1. **db** becomes healthy  
2. **ollama** starts (model pull may continue in background)  
3. **ai-service** starts and talks to ollama  
4. **backend** waits for healthy db, then starts (and uses ai-service)  
5. **frontend** depends on backend  

Request path for chat:

`Browser → frontend → backend /api/v1/chat → ai-service /api/v1/ai/chat → ollama`

Request path for summarise after upload:

`Upload → backend stores file → background processing → extract text → backend → ai-service /summarize → ollama → save summary in PostgreSQL`

---

## Related docs

- [Architecture](./architecture.md)  
- [Development Guide](./development-guide.md)  
