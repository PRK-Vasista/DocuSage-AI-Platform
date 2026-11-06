from __future__ import annotations

import asyncio
import json
import os
import statistics
import time
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any

import aiohttp

try:
    import asyncpg
except ImportError:  # pragma: no cover - optional when direct DB probing is disabled
    asyncpg = None


class ScenarioStats:
    def __init__(self) -> None:
        self._rows: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)

    def record(
        self,
        component: str,
        operation: str,
        status: int | None,
        latency_ms: float,
        error: str | None = None,
    ) -> None:
        key = f"{component}.{operation}"
        self._rows[key].append(
            {
                "status": status,
                "latency_ms": latency_ms,
                "error": error,
            }
        )

    def report(self) -> dict[str, Any]:
        output: dict[str, Any] = {}
        for key, rows in sorted(self._rows.items()):
            latencies = sorted(row["latency_ms"] for row in rows)
            errors = [row for row in rows if row["error"]]
            statuses = Counter(str(row["status"]) for row in rows if row["status"] is not None)
            successes = [row for row in rows if row["status"] is not None and row["status"] < 400]
            output[key] = {
                "requests": len(rows),
                "successful": len(successes),
                "non_successful": len(rows) - len(successes) - len(errors),
                "errors": len(errors),
                "statuses": dict(sorted(statuses.items())),
                "latency_ms": {
                    "min": round(min(latencies), 2) if latencies else None,
                    "p50": round(statistics.median(latencies), 2) if latencies else None,
                    "p95": round(latencies[min(len(latencies) - 1, int(len(latencies) * 0.95))], 2)
                    if latencies
                    else None,
                    "max": round(max(latencies), 2) if latencies else None,
                },
                "first_error": errors[0]["error"] if errors else None,
            }
        return output


class ScenarioClient:
    def __init__(self, session: aiohttp.ClientSession, stats: ScenarioStats):
        self.session = session
        self.stats = stats

    async def request(
        self,
        component: str,
        operation: str,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        json_body: dict[str, Any] | None = None,
        form: aiohttp.FormData | None = None,
    ) -> tuple[int | None, Any, str | None]:
        started = time.perf_counter()
        try:
            async with self.session.request(
                method,
                url,
                headers=headers,
                json=json_body,
                data=form,
            ) as response:
                raw = await response.read()
                try:
                    payload: Any = json.loads(raw.decode("utf-8")) if raw else {}
                except json.JSONDecodeError:
                    payload = raw.decode("utf-8", errors="replace")
                self.stats.record(
                    component,
                    operation,
                    response.status,
                    (time.perf_counter() - started) * 1000,
                )
                return response.status, payload, None
        except Exception as exc:  # noqa: BLE001 - record service failures as test results
            error = f"{type(exc).__name__}: {exc}"
            self.stats.record(
                component,
                operation,
                None,
                (time.perf_counter() - started) * 1000,
                error,
            )
            return None, None, error


async def run_application_scenario() -> int:
    architectures = load_architectures()
    users_per_architecture = int(os.getenv("SCENARIO_USERS", "5"))
    rounds = int(os.getenv("SCENARIO_ROUNDS", "1"))
    concurrency = int(os.getenv("SCENARIO_CONCURRENCY", "5"))
    timeout_seconds = float(os.getenv("SCENARIO_TIMEOUT_SECONDS", "180"))
    run_chat = os.getenv("SCENARIO_RUN_CHAT", "true").lower() in {"1", "true", "yes"}
    processing_wait_seconds = float(os.getenv("SCENARIO_PROCESSING_WAIT_SECONDS", "60"))
    run_ollama_inference = os.getenv("SCENARIO_RUN_OLLAMA_INFERENCE", "true").lower() in {
        "1",
        "true",
        "yes",
    }
    report_path = os.getenv("RESULTS_FILE", "/results/application-crud-report.json")
    started = time.perf_counter()
    architecture_reports: list[dict[str, Any]] = []

    for architecture_name, config in architectures.items():
        report = await run_architecture(
            architecture_name,
            config,
            users_per_architecture,
            rounds,
            concurrency,
            timeout_seconds,
            run_chat,
            run_ollama_inference,
            processing_wait_seconds,
        )
        architecture_reports.append(report)
        print_architecture_report(report)

    report = {
        "mode": "application-crud",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "configuration": {
            "users_per_architecture": users_per_architecture,
            "rounds": rounds,
            "concurrency": concurrency,
            "run_chat": run_chat,
            "run_ollama_inference": run_ollama_inference,
            "processing_wait_seconds": processing_wait_seconds,
        },
        "architectures": architecture_reports,
    }
    if report_path:
        path = os.path.abspath(report_path)
        report_directory = os.path.dirname(path)
        if report_directory:
            os.makedirs(report_directory, exist_ok=True)
        with open(path, "w", encoding="utf-8") as report_file:
            json.dump(report, report_file, indent=2)
            report_file.write("\n")
        print(f"Wrote application scenario report: {path}")

    failed = any(
        operation["errors"] > 0 or operation["non_successful"] > 0
        for architecture in architecture_reports
        for operation in architecture["operations"].values()
    )
    return 1 if failed else 0


def load_architectures() -> dict[str, dict[str, str]]:
    target_file = os.getenv("APPLICATION_TARGETS_FILE", "").strip()
    raw = ""
    if target_file:
        try:
            with open(target_file, encoding="utf-8") as config_file:
                raw = config_file.read()
        except OSError as exc:
            raise ValueError(f"cannot read APPLICATION_TARGETS_FILE: {exc}") from exc
    else:
        raw = os.getenv("APPLICATION_TARGETS_JSON", "")
    if raw:
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            source = "APPLICATION_TARGETS_FILE" if target_file else "APPLICATION_TARGETS_JSON"
            raise ValueError(f"{source} must contain valid JSON") from exc
        if not isinstance(payload, dict) or not payload:
            raise ValueError("APPLICATION_TARGETS_JSON must map architecture names to target objects")
        return payload

    return {
        "default": {
            "backend": os.getenv("BACKEND_URL", "http://host.docker.internal:8000"),
            "ai": os.getenv("AI_SERVICE_URL", "http://host.docker.internal:8100"),
            "frontend": os.getenv("FRONTEND_URL", "http://host.docker.internal:3000"),
            "ollama": os.getenv("OLLAMA_URL", "http://host.docker.internal:11434"),
            "database": os.getenv("DATABASE_URL", ""),
        }
    }


async def run_architecture(
    architecture_name: str,
    config: dict[str, str],
    users: int,
    rounds: int,
    concurrency: int,
    timeout_seconds: float,
    run_chat: bool,
    run_ollama_inference: bool,
    processing_wait_seconds: float,
) -> dict[str, Any]:
    stats = ScenarioStats()
    timeout = aiohttp.ClientTimeout(total=timeout_seconds)
    connector = aiohttp.TCPConnector(limit=max(concurrency * 4, 20))
    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        client = ScenarioClient(session, stats)
        await run_static_service_checks(client, config, run_ollama_inference)
        await run_database_probe(stats, config.get("database", ""))
        semaphore = asyncio.Semaphore(concurrency)

        async def bounded_user(user_number: int) -> None:
            async with semaphore:
                await run_user_workflow(
                    client,
                    config,
                    architecture_name,
                    user_number,
                    rounds,
                    run_chat,
                    processing_wait_seconds,
                )

        await asyncio.gather(*(bounded_user(number) for number in range(users)))

    return {
        "architecture": architecture_name,
        "operations": stats.report(),
    }


async def run_static_service_checks(
    client: ScenarioClient,
    config: dict[str, str],
    run_ollama_inference: bool,
) -> None:
    await client.request("frontend", "root", "GET", f"{config.get('frontend', '').rstrip('/')}/")
    await client.request("backend", "health", "GET", f"{config.get('backend', '').rstrip('/')}/health")
    await client.request("ai-service", "health", "GET", f"{config.get('ai', '').rstrip('/')}/api/v1/ai/health")
    await client.request("ollama", "tags", "GET", f"{config.get('ollama', '').rstrip('/')}/api/tags")
    if run_ollama_inference and config.get("ollama"):
        await client.request(
            "ollama",
            "generate",
            "POST",
            f"{config['ollama'].rstrip('/')}/api/generate",
            json_body={
                "model": os.getenv("OLLAMA_MODEL", "llama3.2:1b"),
                "prompt": "Reply with the single word: load-test.",
                "stream": False,
            },
        )
    await client.request(
        "ai-service",
        "summarize",
        "POST",
        f"{config.get('ai', '').rstrip('/')}/api/v1/ai/summarize",
        json_body={
            "text": "DocuSage load-test document. " * 80,
            "max_chars": 800,
        },
    )
    await client.request(
        "ai-service",
        "chat",
        "POST",
        f"{config.get('ai', '').rstrip('/')}/api/v1/ai/chat",
        json_body={
            "question": "What is the purpose of this test document?",
            "document_context": "This is a dummy document used for controlled load testing.",
            "history": [],
        },
    )


async def run_user_workflow(
    client: ScenarioClient,
    config: dict[str, str],
    architecture_name: str,
    user_number: int,
    rounds: int,
    run_chat: bool,
    processing_wait_seconds: float,
) -> None:
    backend = config.get("backend", "").rstrip("/")
    unique = uuid.uuid4().hex[:12]
    email = f"loadtest-{architecture_name}-{user_number}-{unique}@example.test"
    password = "LoadTestPass123!"
    status, payload, _ = await client.request(
        "backend",
        "auth.register",
        "POST",
        f"{backend}/api/v1/auth/register",
        json_body={"email": email, "password": password},
    )
    if status is None or status >= 400 or not isinstance(payload, dict):
        return

    status, payload, _ = await client.request(
        "backend",
        "auth.login",
        "POST",
        f"{backend}/api/v1/auth/login",
        json_body={"email": email, "password": password},
    )
    token = payload.get("access_token") if isinstance(payload, dict) else None
    if status is None or status >= 400 or not token:
        return
    headers = {"Authorization": f"Bearer {token}"}

    await client.request("backend", "auth.me", "GET", f"{backend}/api/v1/auth/me", headers=headers)
    document_ids: list[int] = []
    for round_number in range(rounds):
        await client.request("backend", "documents.list", "GET", f"{backend}/api/v1/files/", headers=headers)
        form = aiohttp.FormData()
        form.add_field(
            "file",
            (
                f"Dummy load document {round_number}. "
                "This text is generated only for a controlled test. " * 30
            ).encode("utf-8"),
            filename=f"load-test-{unique}-{round_number}.txt",
            content_type="text/plain",
        )
        status, payload, _ = await client.request(
            "backend",
            "documents.create.upload",
            "POST",
            f"{backend}/api/v1/files/upload",
            headers=headers,
            form=form,
        )
        document_id = payload.get("id") if isinstance(payload, dict) else None
        if status is None or status >= 400 or not isinstance(document_id, int):
            continue
        document_ids.append(document_id)
        await client.request("backend", "documents.read", "GET", f"{backend}/api/v1/files/{document_id}", headers=headers)
        summary_status, summary_payload, _ = await client.request(
            "backend",
            "documents.summary.read",
            "GET",
            f"{backend}/api/v1/files/{document_id}/summary",
            headers=headers,
        )
        await client.request("backend", "chat.history.read", "GET", f"{backend}/api/v1/chat/{document_id}", headers=headers)
        ready = (
            summary_status is not None
            and summary_status < 400
            and isinstance(summary_payload, dict)
            and summary_payload.get("processing_status") == "ready"
        )
        if not ready:
            ready = await wait_for_document_ready(
                client,
                backend,
                document_id,
                headers,
                processing_wait_seconds,
            )
        if run_chat and ready:
            await client.request(
                "backend",
                "chat.create",
                "POST",
                f"{backend}/api/v1/chat/{document_id}",
                headers=headers,
                json_body={"question": "What is this dummy document for?"},
            )

    for document_id in document_ids:
        await client.request("backend", "documents.delete.soft", "DELETE", f"{backend}/api/v1/files/{document_id}", headers=headers)
        await client.request(
            "backend",
            "documents.list.trash",
            "GET",
            f"{backend}/api/v1/files/?include_deleted=true",
            headers=headers,
        )
        await client.request(
            "backend",
            "documents.delete.permanent",
            "DELETE",
            f"{backend}/api/v1/files/{document_id}/permanent",
            headers=headers,
        )


async def wait_for_document_ready(
    client: ScenarioClient,
    backend: str,
    document_id: int,
    headers: dict[str, str],
    timeout_seconds: float,
) -> bool:
    deadline = time.perf_counter() + timeout_seconds
    while time.perf_counter() < deadline:
        await asyncio.sleep(1)
        status, payload, _ = await client.request(
            "backend",
            "documents.summary.poll",
            "GET",
            f"{backend}/api/v1/files/{document_id}/summary",
            headers=headers,
        )
        if status is None or status >= 400:
            return False
        if isinstance(payload, dict):
            processing_status = payload.get("processing_status")
            if processing_status == "ready":
                return True
            if processing_status == "failed":
                return False
    return False


async def run_database_probe(stats: ScenarioStats, database_url: str) -> None:
    if not database_url:
        return
    if asyncpg is None:
        stats.record("postgres", "driver", None, 0, "asyncpg is not installed")
        return
    connection = None
    try:
        started = time.perf_counter()
        connection = await asyncpg.connect(database_url)
        stats.record("postgres", "connect", 200, (time.perf_counter() - started) * 1000)
        async with connection.transaction():
            for operation, query in (
                ("create", "CREATE TEMP TABLE load_test_probe (id integer, value text)"),
                ("create.insert", "INSERT INTO load_test_probe VALUES (1, 'dummy')"),
                ("read", "SELECT value FROM load_test_probe WHERE id = 1"),
                ("update", "UPDATE load_test_probe SET value = 'updated' WHERE id = 1"),
                ("delete", "DELETE FROM load_test_probe WHERE id = 1"),
            ):
                operation_started = time.perf_counter()
                await connection.execute(query)
                stats.record("postgres", operation, 200, (time.perf_counter() - operation_started) * 1000)
    except Exception as exc:  # noqa: BLE001 - record database stress failures
        stats.record("postgres", "transaction", None, 0, f"{type(exc).__name__}: {exc}")
    finally:
        if connection is not None:
            await connection.close()


def print_architecture_report(report: dict[str, Any]) -> None:
    print(f"\n=== Architecture: {report['architecture']} ===")
    for operation, metrics in report["operations"].items():
        latency = metrics["latency_ms"]
        print(
            f"{operation}: requests={metrics['requests']} successful={metrics['successful']} "
            f"errors={metrics['errors']} p50_ms={latency['p50']} p95_ms={latency['p95']} "
            f"statuses={metrics['statuses']}"
        )
