# Development Guide

This is Copyright of DocuSage 2026 Owner Rohith Kumar Vasista P.

Practical commands and references for developing DocuSage locally.

---

## Prerequisites

- Docker and Docker Compose  
- Git  

---

## Start the full stack

```bash
git clone https://github.com/PRK-Vasista/DocuSage-AI-Platform.git
cd DocuSage-AI-Platform
cp .env.example .env
# Edit .env for secrets (required for APP_ENV=production)
docker compose up --build -d
```

Configuration is driven by `.env` (see root `.env.example`). Key variables:
`APP_ENV`, `LOG_LEVEL`, `SECRET_KEY`, `POSTGRES_*`, `DATABASE_URL`, `CORS_ORIGINS`,
optional `SMTP_*` for password-reset email.

Check status:

```bash
docker compose ps
```

### Useful URLs

| URL | Purpose |
|-----|---------|
| http://localhost:3000 | Frontend |
| http://localhost:8000/docs | Backend Swagger |
| http://localhost:8000/health | Backend health (DB + AI summary) |
| http://localhost:8100/docs | AI service Swagger |
| http://localhost:8100/api/v1/ai/health | AI health |
| http://localhost:11434 | Ollama (optional debug) |

First boot may take time while `llama3.2:1b` is pulled into Ollama.

```bash
docker compose logs -f ai-service
docker compose exec ollama ollama list
```

---

## Start / log services one by one

Suggested dependency order:

1. `db`  
2. `ollama`  
3. `ai-service`  
4. `backend`  
5. `frontend`  

Continuous logs (separate terminals):

```bash
docker compose logs -f --timestamps db
docker compose logs -f --timestamps ollama
docker compose logs -f --timestamps ai-service
docker compose logs -f --timestamps backend
docker compose logs -f --timestamps frontend
```

---

## Automated tests

Backend:

```bash
docker compose build backend
docker compose run --rm backend pytest -v
```

AI service (Ollama mocked in tests):

```bash
docker compose build ai-service
docker compose run --rm ai-service pytest -v
```

---

## Database migrations (Alembic)

Migrations run automatically when the backend starts.

| Env variable | Default | Purpose |
|--------------|---------|---------|
| `ENABLE_ALEMBIC_MIGRATIONS` | `true` | Run Alembic on startup |
| `ENABLE_CREATE_ALL_FALLBACK` | `true` | Fallback `create_all()` if migrations fail (dev) |
| `DB_MIGRATION_MAX_RETRIES` | `5` | Retries while DB warms up |
| `DB_MIGRATION_RETRY_SECONDS` | `2` | Delay between retries |

```bash
docker compose exec backend alembic current
docker compose exec backend alembic upgrade head
```

**Rule:** Alembic revision IDs must be ≤ **32** characters. The backend validates this before migrating.

---

## API surface (summary)

### Auth — `/api/v1/auth`

| Method | Path | Description |
|--------|------|-------------|
| POST | `/register` | Register + JWT |
| POST | `/login` | Login + JWT |
| GET | `/me` | Current user |
| POST | `/change-password` | Change password (auth) |
| POST | `/forgot-password` | Request reset (SMTP optional) |
| POST | `/reset-password` | Consume reset token |

### Files — `/api/v1/files`

| Method | Path | Description |
|--------|------|-------------|
| POST | `/upload` | Upload + queue processing |
| GET | `/` | List documents |
| GET | `/{id}` | Metadata |
| GET | `/{id}/summary` | Summary + status |
| GET | `/{id}/download` | Download original |
| DELETE | `/{id}` | Soft delete |
| DELETE | `/{id}/permanent` | Permanent delete (trash only) |

### Chat — `/api/v1/chat`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/{document_id}` | History |
| POST | `/{document_id}` | Ask a question |

### AI service (internal) — `/api/v1/ai`

Called by backend only:

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health |
| POST | `/summarize` | Summarize text |
| POST | `/chat` | Grounded chat |

---

## Hot reload notes

- Backend code: `./backend` mounted into the container  
- Frontend source: `./frontend/src` mounted for live reload  
- AI service: `./ai-service` mounted  

Do not commit secrets, `.env` files, or uploaded user documents.

---

## Backups

Volumes: `postgres_data`, `user_files`, `ollama_data`.

```bash
docker compose exec -T db pg_dump -U user docu_sage_db > docusage-backup.sql
```

See also root [PRODUCTION.md](../PRODUCTION.md).

Rate limiting is in-process on a single backend container (not shared across replicas).

---

## Reset

Stop (keep volumes):

```bash
docker compose down
```

Full wipe (DB + uploads + ollama volume data):

```bash
docker compose down --volumes
```

Then:

```bash
docker compose up --build -d
```

---

## Related docs

- [Architecture](./architecture.md)  
- [Services](./services.md)  
- [Evolution](./evolution.md)  
- User guide: [../README.md](../README.md)  
