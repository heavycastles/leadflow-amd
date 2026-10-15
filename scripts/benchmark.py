"""Benchmark the configured LLM endpoint: latency, tok/s, JSON validity, intent accuracy.

Usage (AMD Token Factory, one key):  AMD_TOKEN_FACTORY_API_KEY=rc-... python -m scripts.benchmark --concurrency 2
Usage (vLLM on MI300X, optional):    LLM_BACKEND=openai LLM_BASE_URL=http://<ip>:8000/v1 python -m scripts.benchmark
Shared Token Factory endpoints are rate-limited per key/IP, so keep concurrency low there.
"""

from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor

from app.agent import sanitize
from app.llm import LLMClient

CASES = [
    ("Хочу заказать 2 шт кроссовки 42 размера, срочно", "order"),
    ("Salom! 3 dona kurtka kerak, narxi qancha?", "quote"),
    ("What is the price for 50 hoodies with logo?", "quote"),
    ("I want to order 4 bottles of olive oil, deliver today", "order"),
    ("Kurtka brak keldi, pulni qaytaring", "complaint"),
    ("Crypto bonus casino click here", "spam"),
    ("Вы работаете в воскресенье?", "question"),
    ("Сколько стоит доставка в Самарканд?", "quote"),
]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--concurrency", type=int, default=8)
    p.add_argument("--rounds", type=int, default=4)
    args = p.parse_args()
    client = LLMClient()
    jobs = CASES * args.rounds
    t0 = time.perf_counter()
    with ThreadPoolExecutor(args.concurrency) as pool:
        results = list(pool.map(lambda c: (c[1], client.analyze(c[0])), jobs))
    wall = time.perf_counter() - t0
    tokens = sum(r.completion_tokens for _, r in results)
    correct = sum(sanitize(r.data)["intent"] == exp for exp, r in results)
    report = {
        "llm": client.info, "requests": len(results), "concurrency": args.concurrency,
        "wall_s": round(wall, 2), "req_per_s": round(len(results) / wall, 2),
        "aggregate_tokens_per_s": round(tokens / wall, 1),
        "avg_latency_ms": round(sum(r.latency_ms for _, r in results) / len(results), 1),
        "fallbacks": sum(1 for _, r in results if r.fallback_reason),
        "intent_accuracy": round(correct / len(results), 3),
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
