from __future__ import annotations

import asyncio
import json
import os
import statistics
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import aiohttp


@dataclass
class Result:
    status: int | None
    latency_ms: float
    error: str | None = None


def env_int(name: str, default: int, minimum: int = 0) -> int:
    value = int(os.getenv(name, str(default)))
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    return value


def env_float(name: str, default: float, minimum: float = 0.0) -> float:
    value = float(os.getenv(name, str(default)))
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    return value


def parse_json_env(name: str, default: Any) -> Any:
    raw = os.getenv(name, "")
    if not raw:
        return default
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{name} must contain valid JSON") from exc


async def main() -> int:
    if os.getenv("LOAD_MODE", "http").lower() == "application-crud":
        from application_scenario import run_application_scenario

        return await run_application_scenario()

    method = os.getenv("HTTP_METHOD", "GET").upper()
    request_count = env_int("REQUESTS", 100, minimum=1)
    duration_seconds = env_float("DURATION_SECONDS", 0.0)
    concurrency = env_int("CONCURRENCY", 10, minimum=1)
    requests_per_second = env_float("REQUESTS_PER_SECOND", 10.0, minimum=0.0)
    timeout_seconds = env_float("TIMEOUT_SECONDS", 10.0, minimum=0.1)
    headers = parse_json_env("REQUEST_HEADERS", {})
    body = os.getenv("REQUEST_BODY", "")
    fail_on_error = os.getenv("FAIL_ON_ERROR", "true").lower() in {"1", "true", "yes"}
    results_file = os.getenv("RESULTS_FILE", "").strip()

    targets_payload = parse_json_env("TARGETS_JSON", None)
    if targets_payload is None:
        targets = {
            "single-target": os.getenv(
                "TARGET_URL", "http://host.docker.internal:8000/health"
            )
        }
    elif isinstance(targets_payload, dict):
        targets = targets_payload
    else:
        raise ValueError("TARGETS_JSON must be a JSON object of name to URL")

    if not targets or any(not isinstance(name, str) or not isinstance(url, str) or not url for name, url in targets.items()):
        raise ValueError("TARGETS_JSON must contain non-empty target names and URLs")

    target_reports: list[dict[str, Any]] = []

    for target_name, target_url in targets.items():
        results, elapsed_seconds = await run_target(
            target_name=target_name,
            target_url=target_url,
            method=method,
            request_count=request_count,
            duration_seconds=duration_seconds,
            concurrency=concurrency,
            requests_per_second=requests_per_second,
            timeout_seconds=timeout_seconds,
            headers=headers,
            body=body,
        )
        report = summarize_results(target_name, target_url, results, elapsed_seconds)
        target_reports.append(report)
        print_report(report)

    combined_report = {
        "method": method,
        "targets": target_reports,
        "configuration": {
            "requests": request_count,
            "duration_seconds": duration_seconds,
            "concurrency": concurrency,
            "requests_per_second": requests_per_second,
            "timeout_seconds": timeout_seconds,
        },
    }
    print(f"\nCompleted load collection for {len(target_reports)} target(s).")
    if results_file:
        output_path = Path(results_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(combined_report, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote combined report: {output_path}")

    has_failures = any(report["errors"] > 0 or report["non_successful"] > 0 for report in target_reports)
    has_empty_target = any(report["successful"] == 0 for report in target_reports)
    return 1 if has_empty_target or (fail_on_error and has_failures) else 0


async def run_target(
    *,
    target_name: str,
    target_url: str,
    method: str,
    request_count: int,
    duration_seconds: float,
    concurrency: int,
    requests_per_second: float,
    timeout_seconds: float,
    headers: dict[str, Any],
    body: str,
) -> tuple[list[Result], float]:
    queue: asyncio.Queue[int | None] = asyncio.Queue(maxsize=concurrency * 2)
    results: list[Result] = []
    started = time.perf_counter()
    deadline = started + duration_seconds if duration_seconds > 0 else None

    print(
        f"\nStarting target '{target_name}': method={method} url={target_url} concurrency={concurrency} "
        f"rps={requests_per_second or 'unlimited'} requests="
        f"{request_count if deadline is None else 'until duration'}"
    )

    timeout = aiohttp.ClientTimeout(total=timeout_seconds)
    connector = aiohttp.TCPConnector(limit=concurrency)

    async def request_one(session: aiohttp.ClientSession) -> None:
        request_started = time.perf_counter()
        try:
            request_kwargs: dict[str, Any] = {"headers": headers}
            if body:
                request_kwargs["data"] = body
            async with session.request(method, target_url, **request_kwargs) as response:
                await response.read()
                results.append(
                    Result(
                        status=response.status,
                        latency_ms=(time.perf_counter() - request_started) * 1000,
                    )
                )
        except Exception as exc:  # noqa: BLE001 - report request failures as load results
            results.append(
                Result(
                    status=None,
                    latency_ms=(time.perf_counter() - request_started) * 1000,
                    error=f"{type(exc).__name__}: {exc}",
                )
            )

    async def worker(session: aiohttp.ClientSession) -> None:
        while True:
            item = await queue.get()
            try:
                if item is None:
                    return
                await request_one(session)
            finally:
                queue.task_done()

    async def producer() -> None:
        sent = 0
        interval = 1.0 / requests_per_second if requests_per_second > 0 else 0.0
        next_request_at = time.perf_counter()
        while (deadline is None and sent < request_count) or (
            deadline is not None and time.perf_counter() < deadline
        ):
            await queue.put(sent)
            sent += 1
            if interval:
                next_request_at += interval
                await asyncio.sleep(max(0.0, next_request_at - time.perf_counter()))
        for _ in range(concurrency):
            await queue.put(None)

    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        workers = [asyncio.create_task(worker(session)) for _ in range(concurrency)]
        await producer()
        await queue.join()
        await asyncio.gather(*workers)

    return results, time.perf_counter() - started


def summarize_results(
    target_name: str,
    target_url: str,
    results: list[Result],
    elapsed_seconds: float,
) -> dict[str, Any]:
    statuses = Counter(str(result.status) for result in results if result.status is not None)
    failures = [result for result in results if result.error]
    latencies = [result.latency_ms for result in results]
    successful = [result for result in results if result.status is not None and result.status < 400]

    ordered = sorted(latencies)
    return {
        "name": target_name,
        "url": target_url,
        "requests": len(results),
        "successful": len(successful),
        "non_successful": len(results) - len(successful) - len(failures),
        "errors": len(failures),
        "statuses": dict(sorted(statuses.items())),
        "elapsed_seconds": round(elapsed_seconds, 3),
        "throughput_requests_per_second": round(len(results) / elapsed_seconds, 2)
        if elapsed_seconds
        else 0,
        "latency_ms": {
            "min": round(min(ordered), 2) if ordered else None,
            "p50": round(statistics.median(ordered), 2) if ordered else None,
            "p95": round(ordered[min(len(ordered) - 1, int(len(ordered) * 0.95))], 2)
            if ordered
            else None,
            "max": round(max(ordered), 2) if ordered else None,
        },
        "first_error": failures[0].error if failures else None,
    }


def print_report(report: dict[str, Any]) -> None:
    print(f"Completed '{report['name']}': {report['requests']} requests in {report['elapsed_seconds']:.2f}s")
    print(f"Throughput: {report['throughput_requests_per_second']:.2f} requests/s")
    print(f"Statuses: {report['statuses']}")
    print(f"Errors: {report['errors']}")
    latency = report["latency_ms"]
    print(
        "Latency ms: "
        f"min={latency['min']} p50={latency['p50']} "
        f"p95={latency['p95']} max={latency['max']}"
    )
    if report["first_error"]:
        print(f"First error: {report['first_error']}")


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(main()))
    except (ValueError, KeyboardInterrupt) as exc:
        print(f"load-test configuration error: {exc}")
        raise SystemExit(2)
