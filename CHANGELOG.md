# Changelog

This is Copyright of DocuSage 2026 Owner Rohith Kumar Vasista P.

All notable changes to DocuSage AI Platform are documented here.

## [1.0.0] — pending

Final release checks only (version tag / checklist confirmation).  
**No new feature code expected.** Wait for an explicit release command before tagging/pushing `v1.0.0`.

## [0.9.0] — 2026-07-14

Auth polish and friend/local production readiness package (almost everything for release).

### Added
- Authenticated change-password
- Forgot/reset password with hashed one-time tokens
- Optional SMTP via Python stdlib (`SMTP_*` in `.env`)
- Production checklist document
- Consolidated release documentation for the hardening path

## [0.8.0] — 2026-07-14

Reliability, ops, and AI readiness UX.

### Added
- Backend `GET /health` (DB + AI summary)
- AI health includes model readiness messaging
- Compose healthchecks and `service_healthy` dependencies
- In-process rate limiting (auth, upload, chat)
- Workspace AI health banner and chat retry/dismiss
- Backup/restore guidance for Docker volumes

## [0.7.0] — 2026-07-14

Secrets, configuration, and logging hardening.

### Added
- Root `.env.example` and Compose `env_file` / `${VAR}` interpolation
- `APP_ENV`, `LOG_LEVEL`, `CORS_ORIGINS`
- Production fail-closed checks for weak `SECRET_KEY` / sample DB password
- Developer documentation set (architecture, services, evolution, guide)

### Changed
- Logging controlled by `LOG_LEVEL` (removed per-module forced DEBUG)
- Alembic URL placeholder; runtime uses `DATABASE_URL`

## [0.6.0] — enhancement

Cursor-style workspace UI, light/dark theme, summary + chat layout.

## [0.5.0] — sprint

Isolated AI unit (Ollama), AI summary, per-document chat.

## [0.4.0] — sprint

Extraction pipeline, background processing, extractive summary, status UI.

## [0.3.0] — sprint

Upload, trash, permanent delete, quota, modular code, Alembic.
