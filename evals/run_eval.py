# This is Copyright of DocuSage 2026 Owner Rohith Kumar Vasista P.

"""
DocuSage evaluation runner (stdlib only).

Modes:
  offline — no Ollama; stub answers from the golden set (validates harness + metrics)
  live    — call running backend AI via ai-service HTTP (optional)

Examples:
  python evals/run_eval.py
  python evals/run_eval.py --mode live --ai-url http://localhost:8100
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

from metrics import score_item, summarize_latencies

ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / "fixtures"
DOCS_DIR = FIXTURES / "sample_docs"
GOLDEN_PATH = FIXTURES / "golden_qa.json"
REPORT_MD = ROOT / "latest_report.md"
REPORT_JSON = ROOT / "latest_report.json"

_REFUSAL = (
    "I don't know based on the document. That detail is not mentioned in the "
    "provided context."
)


def load_docs() -> dict[str, str]:
    docs: dict[str, str] = {}
    for path in sorted(DOCS_DIR.glob("*.txt")):
        docs[path.name] = path.read_text(encoding="utf-8")
    return docs


def load_golden() -> dict:
    return json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))


def offline_answer(item: dict, context: str) -> str:
    """
    Deterministic stub: answerable → short context-grounded reply;
    unanswerable → abstention.
    """
    if not item.get("answerable", True):
        return _REFUSAL
    # Prefer first matching keyword that appears in context, else a grounded snippet.
    keywords = item.get("must_include_any") or []
    hits = [k for k in keywords if k.lower() in context.lower()]
    snippet = context.strip().split("\n")[0][:180]
    if hits:
        return f"According to the document: {', '.join(hits)}. Context: {snippet}"
    return f"According to the document: {snippet}"


def live_chat(ai_url: str, question: str, context: str, timeout: float = 180.0) -> str:
    url = f"{ai_url.rstrip('/')}/api/v1/ai/chat"
    body = json.dumps(
        {
            "question": question,
            "document_context": context,
            "history": [],
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return (payload.get("answer") or "").strip()


def live_summarize(ai_url: str, text: str, timeout: float = 180.0) -> str:
    url = f"{ai_url.rstrip('/')}/api/v1/ai/summarize"
    body = json.dumps({"text": text}).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return (payload.get("summary") or "").strip()


def run_eval(*, mode: str, ai_url: str) -> dict:
    docs = load_docs()
    golden = load_golden()
    items = golden["items"]

    contexts: dict[str, str] = {}
    summarize_ms: list[float] = []
    for name, text in docs.items():
        if mode == "live":
            started = time.perf_counter()
            try:
                contexts[name] = live_summarize(ai_url, text) or text
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
                contexts[name] = text
                print(f"warn: summarize failed for {name}: {exc}; using full text")
            summarize_ms.append((time.perf_counter() - started) * 1000.0)
        else:
            # Offline uses the document itself as the "summary context".
            contexts[name] = text
            summarize_ms.append(0.0)

    rows: list[dict] = []
    chat_ms: list[float] = []
    for item in items:
        doc_name = item["doc"]
        context = contexts[doc_name]
        started = time.perf_counter()
        if mode == "live":
            try:
                answer = live_chat(ai_url, item["question"], context)
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
                answer = f"ERROR: {exc}"
        else:
            answer = offline_answer(item, context)
        elapsed = (time.perf_counter() - started) * 1000.0
        chat_ms.append(elapsed)

        scored = score_item(
            answerable=bool(item.get("answerable", True)),
            answer=answer,
            context=context,
            must_include_any=item.get("must_include_any") or [],
        )
        rows.append(
            {
                "id": item["id"],
                "doc": doc_name,
                "question": item["question"],
                "answerable": item.get("answerable", True),
                "answer": answer,
                "duration_ms": round(elapsed, 2),
                **scored,
            }
        )

    answerable = [r for r in rows if r["answerable"]]
    unanswerable = [r for r in rows if not r["answerable"]]
    grounded_rate = (
        sum(1 for r in answerable if r["grounded"]) / len(answerable) if answerable else 0.0
    )
    keyword_rate = (
        sum(1 for r in answerable if r["keywords_ok"]) / len(answerable) if answerable else 0.0
    )
    answerable_success = (
        sum(1 for r in answerable if r["success"]) / len(answerable) if answerable else 0.0
    )
    abstention_rate = (
        sum(1 for r in unanswerable if r["abstained"]) / len(unanswerable)
        if unanswerable
        else 0.0
    )

    report = {
        "mode": mode,
        "ai_url": ai_url if mode == "live" else None,
        "item_count": len(rows),
        "answerable_count": len(answerable),
        "unanswerable_count": len(unanswerable),
        "groundedness_proxy_rate": round(grounded_rate, 4),
        "keyword_hit_rate": round(keyword_rate, 4),
        "answerable_success_rate": round(answerable_success, 4),
        "abstention_rate_on_unanswerable": round(abstention_rate, 4),
        "chat_latency": summarize_latencies(chat_ms),
        "summarize_latency": summarize_latencies(summarize_ms),
        "notes": [
            "Groundedness is token-overlap with context (proxy), not formal NLI.",
            "Offline mode stubs answers to validate the harness; live mode needs ai-service.",
            "Chat in the product uses stored summaries — same grounding idea as this eval.",
        ],
        "items": rows,
    }
    return report


def write_reports(report: dict) -> None:
    REPORT_JSON.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    chat = report["chat_latency"]
    summ = report["summarize_latency"]
    lines = [
        "# DocuSage eval report",
        "",
        f"- Mode: `{report['mode']}`",
        f"- Items: {report['item_count']} "
        f"({report['answerable_count']} answerable / {report['unanswerable_count']} unanswerable)",
        f"- Groundedness proxy (answerable): **{report['groundedness_proxy_rate'] * 100:.1f}%**",
        f"- Keyword hit rate (answerable): **{report['keyword_hit_rate'] * 100:.1f}%**",
        f"- Answerable success: **{report['answerable_success_rate'] * 100:.1f}%**",
        f"- Abstention on unanswerable: **{report['abstention_rate_on_unanswerable'] * 100:.1f}%**",
        f"- Chat latency p50/p95: **{chat['p50_ms']} / {chat['p95_ms']} ms**",
        f"- Summarize latency p50/p95: **{summ['p50_ms']} / {summ['p95_ms']} ms**",
        "",
        "## Notes",
        "",
    ]
    for note in report["notes"]:
        lines.append(f"- {note}")
    lines.append("")
    lines.append("Regenerate with `python3 evals/run_eval.py` (offline) or "
                 "`python3 evals/run_eval.py --mode live`.")
    lines.append("")
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run DocuSage eval harness")
    parser.add_argument("--mode", choices=("offline", "live"), default="offline")
    parser.add_argument("--ai-url", default="http://localhost:8100")
    args = parser.parse_args()

    report = run_eval(mode=args.mode, ai_url=args.ai_url)
    write_reports(report)
    print(f"Wrote {REPORT_MD}")
    print(f"Wrote {REPORT_JSON}")
    print(
        "groundedness_proxy={g:.1%} abstention={a:.1%} chat_p50_ms={p50}".format(
            g=report["groundedness_proxy_rate"],
            a=report["abstention_rate_on_unanswerable"],
            p50=report["chat_latency"]["p50_ms"],
        )
    )


if __name__ == "__main__":
    main()
