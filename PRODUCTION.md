# Production checklist (v1.1 — friend/local Docker)

This is Copyright of DocuSage 2026 Owner Rohith Kumar Vasista P.

Use this before sharing a Docker deploy with others on a private machine or LAN.
This release does **not** include a public reverse proxy or TLS terminator.

## Before first start

1. Copy env template and edit secrets:
   ```bash
   cp .env.example .env
   ```
2. Set a strong JWT secret (32+ random characters):
   ```bash
   openssl rand -hex 32
   ```
   Put the value in `SECRET_KEY`.
3. Change `POSTGRES_PASSWORD` and update `DATABASE_URL` to match.
4. For shared/always-on use set:
   - `APP_ENV=production`
   - `LOG_LEVEL=INFO`
5. Set `CORS_ORIGINS` to the exact browser origin(s) you use (e.g. `http://192.168.1.10:3000`).
6. Optional password-reset email: set `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`, and `PUBLIC_APP_URL`. Leave `SMTP_HOST` empty if you only need change-password while logged in.
7. Optional AI retry tuning (defaults are fine for most installs):
   - `AI_SUMMARIZE_MAX_ATTEMPTS` (default `3`)
   - `AI_SUMMARIZE_RETRY_SECONDS` (default `1.5`)

## Start

```bash
docker compose up --build -d
```

Open http://localhost:3000 (or your host IP on port 3000).

First boot may take several minutes while Ollama pulls `llama3.2:1b`.

## Verify

- Frontend loads and registration/login works
- `curl http://localhost:8000/health` shows database `ok`
- `curl http://localhost:8100/api/v1/ai/health` shows model availability (may be `degraded` until pull finishes)
- Upload a small PDF/TXT → status becomes Ready → summary + chat work
- If processing fails, Failed reason is visible and **Retry processing** works without re-upload

## Backups (volumes)

DocuSage data lives in Docker volumes: `postgres_data`, `user_files`, and optionally `ollama_data`.

Example Postgres dump:

```bash
docker compose exec -T db pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > docusage-backup.sql
```

Restore (example):

```bash
cat docusage-backup.sql | docker compose exec -T db psql -U "$POSTGRES_USER" "$POSTGRES_DB"
```

Uploaded files volume can be archived with `docker run --rm -v <project>_user_files:/data -v "$PWD":/backup alpine tar czf /backup/user_files.tgz -C /data .`

## Not in this release (deferred)

- Public HTTPS / reverse proxy
- Mandatory email verification on register
- Third-party email SDKs
- Multi-replica shared rate-limit store
- Vector RAG / Redis / OpenTelemetry
