# LeadFlow AI — mock-backend benchmark (NOT MI300X)

**Label: MOCK only.** These numbers come from `LLM_BACKEND=mock` (deterministic offline analyzer in `app/llm.py`).
They are **not** measurements on AMD Instinct MI300X / vLLM / ROCm.

Live numbers on AMD come from the Token Factory API once `AMD_TOKEN_FACTORY_API_KEY` is set (`python -m app.llm`, `python -m scripts.benchmark --concurrency 2`). Self-hosted MI300X numbers stay **TBD** until (optional) AMD Developer Cloud credits are claimed and `scripts/benchmark.py` is run against vLLM on MI300X. Token Factory API access alone is enough to participate — credits are only for real MI300X benches. Do not treat mock latency or tok/s as submission hardware evidence.

## How this was produced

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
LLM_BACKEND=mock python -m scripts.benchmark --concurrency 8 --rounds 4
```

Date: 2026-10-15 (Europe/Moscow). Host: local Linux box (no GPU path exercised).

## Results (mock)

| field | value | notes |
|---|---|---|
| backend | `mock` | not openai/vLLM |
| model (configured) | Qwen/Qwen2.5-7B-Instruct | name only; mock does not load weights |
| requests | 32 | 8 cases × 4 rounds |
| concurrency | 8 | ThreadPoolExecutor |
| wall_s | ~0.0 | rounded; mock is CPU-instant |
| req/s | ~10k (order of magnitude) | **not meaningful** — no network/GPU |
| aggregate tok/s | 0.0 | mock does not emit token counts |
| avg latency_ms | ~0.0 | **not meaningful** for mock |
| fallbacks | 0 | mock path, not fallback-from-GPU |
| intent_accuracy | **1.000** | on the fixed 8-case suite (RU/UZ/EN) |

Raw JSON from one run:

```json
{
  "llm": {
    "backend": "mock",
    "base_url": "http://localhost:8000/v1",
    "model": "Qwen/Qwen2.5-7B-Instruct",
    "hardware": "AMD Instinct MI300X (ROCm, vLLM)",
    "fallback": true
  },
  "requests": 32,
  "concurrency": 8,
  "wall_s": 0.0,
  "req_per_s": 9787.38,
  "aggregate_tokens_per_s": 0.0,
  "avg_latency_ms": 0.0,
  "fallbacks": 0,
  "intent_accuracy": 1.0
}
```

Note: `llm.hardware` is the default env label (`LLM_HARDWARE`); with `LLM_BACKEND=mock` it does **not** mean MI300X ran. Intent accuracy is the only metric that is useful here (sanity of the offline analyzer + `sanitize()`).

## After AMD cloud (fill later)

```bash
LLM_BACKEND=openai LLM_BASE_URL=http://<mi300x-ip>:8000/v1 \
  python -m scripts.benchmark --concurrency 8 --rounds 4
```

Paste results into the MI300X table in `README.md` and optionally add `docs/benchmarks-mi300x.md`. Keep this mock file as a CI/local reference only.
