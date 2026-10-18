# Live proof — AMD Token Factory (2026-10-18)

LeadFlow AI running against the **AMD Token Factory** OpenAI-compatible API — no mock, no fallbacks.

| | |
|---|---|
| Base URL | `https://developer.amd.com.cn/radeon/api/v1` |
| Model | `DeepSeek-V4-Flash` (picked from `GET /models`; also tried Qwen3.8-Flash-Next, Gemma-4-31B-IT — slower) |
| Hardware | AMD Radeon cloud GPUs (Token Factory) |
| How | `./scripts/go_live.sh rc-…` → `python serve.py` → `./scripts/demo.sh` |

## `./scripts/go_live.sh --check`
```json
{ "backend": "openai", "provider": "amd-token-factory", "model": "DeepSeek-V4-Flash",
  "model_available": true, "sample": { "intent": "quote", "language": "uz", "latency_ms": 9206.5, "completion_tokens": 145 },
  "ok": true }
```

## `./scripts/demo.sh` — 5 leads, RU / UZ / EN (score | name | intent | action | backend | latency | AI reply)
```
100 | Ivan    | order     | create_order_draft | openai | 18498ms | Здравствуйте! Спасибо за заказ. Уточните, пожалуйста, модель…
85  | Dilnoza | order     | send_quote         | openai | 16398ms | Assalomu alaykum! 3 dona kurtka uchun narxni bilish uchun yo…
70  | Sarah   | quote     | send_quote         | openai |  5650ms | Thank you for your inquiry! We will prepare a quote for 50 h…
60  | Aziz    | complaint | escalate           | openai |  7475ms | Kechirasiz, kurtka sifati bilan bog'liq muammo uchun uzr so'…
0   | Bot     | spam      | ignore             | openai |  4755ms | Sorry, we don't handle such requests. How can I help you wit…

orders:  [{"lead_id":1,"items":[{"name":"кроссовки","qty":2}],"budget":900000.0,"currency":"сум","status":"draft"}]
metrics: {"calls":5,"completion_tokens":716,"fallbacks":0,"avg_latency_ms":10555.1,"avg_tokens_per_sec":13.6,
          "llm":{"provider":"amd-token-factory","model":"DeepSeek-V4-Flash"}}
```

## `python -m scripts.benchmark --concurrency 2 --rounds 1`
8 requests (RU/UZ/EN), 0 fallbacks, intent accuracy **0.875**, aggregate **29.4 tok/s**, avg latency **8.5 s**,
0.22 req/s. Raw: [`live-benchmark-tokenfactory.json`](live-benchmark-tokenfactory.json).
Shared public endpoint, so latency includes queueing; dedicated MI300X numbers remain *pending*.

## Dashboard
Inbox — Uzbek lead answered live by DeepSeek-V4-Flash on AMD Token Factory:

![inbox](live-proof-inbox.png)

AMD · Model — backend, telemetry, measured Token Factory benchmark:

![model](live-proof-model.png)
