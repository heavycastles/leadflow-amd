# LeadFlow AI — commerce lead & order agent on AMD

Small shops in Central Asia get dozens of messages a day in Russian, Uzbek and English from Telegram, WhatsApp
and the web. LeadFlow AI reads every message with an open LLM served on **AMD GPUs — the AMD Token Factory API**
(one key, OpenAI-compatible) or, optionally, **vLLM on an AMD Instinct MI300X (ROCm)** for self-hosted benchmarks —
extracts intent / products / quantities / budget / urgency, drafts a reply in the customer's language, creates an
order draft, and ranks leads with an **explainable hybrid score** (deterministic rules + model features).
An n8n workflow wires it to a Telegram shop bot.

Built for the lablab.ai **AMD Developer Hackathon: ACT III** (track: Reinvent Commerce). MIT licensed.

## Architecture

```
Telegram / WhatsApp / Web form
        │  (n8n workflow: n8n/telegram-leadflow.json)
        ▼
FastAPI  ── POST /leads ──► LeadStore (normalize, de-dupe, rule score)        app/leads.py
        │                         │
        │                         ▼
        │                 CommerceAgent                                       app/agent.py
        │                   ├─ LLMClient ──► OpenAI-compatible /v1/chat/completions   app/llm.py
        │                   │                 = AMD Token Factory API (AMD_TOKEN_FACTORY_API_KEY)
        │                   │                   or vLLM on AMD Instinct MI300X (ROCm, optional)
        │                   │                 (mock fallback when the endpoint is unreachable)
        │                   ├─ sanitize()   strict validation of model JSON
        │                   ├─ hybrid_score() rules + model features + reasons
        │                   └─ order drafts
        ▼
Web dashboard (/)  · /leads · /orders · /metrics (latency, tok/s, backend, fallbacks)
```

Design choices:
- **One key to go live on AMD**: set `AMD_TOKEN_FACTORY_API_KEY` (alias `RADEON_API_KEY`) and the app calls the
  AMD Token Factory API at `https://developer.amd.com.cn/radeon/api/v1` with `DeepSeek-V4-Flash` by default.
- **LLM is pluggable via env** (`LLM_BACKEND`, `LLM_BASE_URL`, `LLM_MODEL`, `LLM_API_KEY` — explicit values always
  win). Any OpenAI-compatible server works, e.g. vLLM on AMD Developer Cloud MI300X for real GPU benchmarks.
- **No LLM-only decisions**: model output is validated and clamped, and the score always shows *why*.
- **Graceful degradation**: if the LLM endpoint is down (or no key is set), a deterministic offline analyzer answers and the UI
  marks the result as FALLBACK (disable with `LLM_FALLBACK=0`).

## AMD usage

| Layer | AMD technology |
|---|---|
| Primary inference | **AMD Token Factory** public model API (AMD GPUs, OpenAI-compatible) — `DeepSeek-V4-Flash` default, any id from `/models` |
| Optional self-hosted | AMD Instinct **MI300X** (192 GB HBM3) on **AMD Developer Cloud**, **ROCm** + `rocm/vllm`, `Qwen/Qwen2.5-7B-Instruct` |
| What runs on AMD | every lead analysis: intent classification, entity extraction, multilingual reply drafting |
| Measured | `scripts/benchmark.py` — latency, aggregate tok/s under concurrency, JSON validity, intent accuracy |

Token Factory alone is enough to run and submit (`python -m app.llm` prints live latency for one sample;
`python -m scripts.benchmark` works against it too). Self-hosted MI300X numbers are an optional extra —
filled in only if Developer Cloud credits are used:

| model | concurrency | req/s | aggregate tok/s | avg latency | intent accuracy |
|---|---|---|---|---|---|
| Qwen2.5-7B-Instruct (MI300X, optional) | 8 | TBD | TBD | TBD | TBD |

Local **mock** backend sanity run (not GPU): see [`docs/benchmarks-mock.md`](docs/benchmarks-mock.md) — intent accuracy only; latency/tok/s are not meaningful without a real AMD endpoint.

## Setup

### 1. Local (no GPU, mock LLM)
```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
python serve.py            # http://localhost:8080
./scripts/demo.sh          # feeds 5 multilingual sample leads
```

### 2. AMD Token Factory API (primary — one key, no card / no $100 credit)
Per lablab ACT III FAQ (2026-10-15): the event is hosted on [notebooks.amd.com/tokenfactory](https://notebooks.amd.com/tokenfactory). Sign up there, open **Public Free Model APIs**, pick a model and copy your API key (`rc-...`) — **no billing or credit card**. Developers do **not** need the $100 Developer Cloud credit to participate. One key covers every shared model.

| | |
|---|---|
| Base URL | `https://developer.amd.com.cn/radeon/api/v1` (OpenAI-compatible `/chat/completions`, `/models`) |
| Auth | `Authorization: Bearer <key>` — env `AMD_TOKEN_FACTORY_API_KEY` (or `RADEON_API_KEY`, as in the AMD docs) |
| Default model | `DeepSeek-V4-Flash` — override with `AMD_TOKEN_FACTORY_MODEL` (or `LLM_MODEL`), e.g. `DeepSeek-V4.1-Flash`, `GLM-5.3-Flash`, `Qwen3.8-27B` |

```bash
./scripts/go_live.sh rc-YOUR_KEY   # writes .env, runs python -m app.llm (never prints the key)
# optional: ./scripts/go_live.sh rc-YOUR_KEY --demo   # also serve.py + scripts/demo.sh
python serve.py                    # dashboard /metrics → backend=openai, provider=amd-token-factory
```
Manual equivalent: `cp .env.example .env`, set `AMD_TOKEN_FACTORY_API_KEY=rc-...`, then `python -m app.llm`.
Or without a file: `AMD_TOKEN_FACTORY_API_KEY=rc-... python serve.py`.
Rules: an explicit `LLM_BACKEND=mock` still forces the offline mock; explicit `LLM_BASE_URL` / `LLM_MODEL` /
`LLM_API_KEY` win over the Token Factory defaults. If a model rejects `response_format`, set `LLM_JSON_MODE=0`.
Shared endpoints are rate-limited per key/IP with a daily cap; the app falls back to the mock (marked FALLBACK)
if a call fails.

### 3. vLLM on AMD Developer Cloud (MI300X — optional, for real GPU benchmarks)
Requires optional $100 Developer Cloud credits ([developer.amd.com/ai-developer-program](https://developer.amd.com/ai-developer-program/) via [login.amd.com](https://login.amd.com)) only if you want measured MI300X latency/tok/s. Not required to submit.
```bash
# on the GPU droplet (ROCm image)
export HF_TOKEN=...           # if the model is gated
./deploy/vllm-rocm.sh         # serves http://<droplet-ip>:8000/v1
```
Then point the app at it (explicit `LLM_*` win over a Token Factory key):
```bash
cp .env.example .env
# LLM_BACKEND=openai
# LLM_BASE_URL=http://<droplet-ip>:8000/v1
# LLM_MODEL=Qwen/Qwen2.5-7B-Instruct
python serve.py
LLM_BACKEND=openai LLM_BASE_URL=http://<droplet-ip>:8000/v1 python -m scripts.benchmark --concurrency 8
```
Tip: run the app on the same droplet and keep port 8000 firewalled, or start vLLM with `VLLM_API_KEY`.

### 4. docker-compose (app + n8n)
```bash
docker compose up --build                    # app :8080, n8n :5678 (uses AMD_TOKEN_FACTORY_API_KEY from .env if set)
LLM_BACKEND=openai LLM_BASE_URL=http://vllm:8000/v1 \
  docker compose --profile amd up --build    # also starts vLLM on the local AMD GPU
```
In n8n: import `n8n/telegram-leadflow.json`, add Telegram credentials, set `OWNER_CHAT_ID`, activate.

## Preflight (before user ship)

```bash
./scripts/preflight_submit.sh   # tests, LICENSE, render.yaml, demo video, prints USER checklist
```

## Deploy demo (Render)

One-click free-tier demo (mock LLM — boots without a GPU). Config: `render.yaml`.

1. Push this repo to GitHub as a **public** repo (e.g. `heavycastles/leadflow-amd`).
2. Open [Render Blueprint](https://dashboard.render.com/select-repo?type=blueprint), connect the repo, Apply.
3. Render builds the `Dockerfile`, sets `LLM_BACKEND=mock`, health-checks `/healthz` on port 8080.
   For a live AMD demo instead: in the Render dashboard add secret env `AMD_TOKEN_FACTORY_API_KEY`, delete
   `LLM_BACKEND` and `LLM_HARDWARE` (the key then selects Token Factory; failures still fall back to mock).
4. Demo URL → paste into `SUBMISSION.md` Links.

Local smoke check of the same image:
```bash
docker build -t leadflow-amd .
docker run --rm -p 8080:8080 -e LLM_BACKEND=mock leadflow-amd
# curl http://localhost:8080/healthz
```

The live AMD path is Token Factory (Setup §2, one key). Self-hosted MI300X + vLLM (Setup §3) is optional and needs Developer Cloud credits for a GPU droplet — do not point the free Render service at a private GPU endpoint unless you firewall it. **Credits are optional:** the hackathon FAQ says Token Factory API alone is enough to participate; $100 credits are only needed for real MI300X benchmarks.

## API
| Method | Path | |
|---|---|---|
| POST | `/leads` | create lead (+ agent analysis); duplicates by email/phone are merged |
| POST | `/leads/{id}/analyze` | re-run the agent |
| GET | `/leads?min_score=` | ranked leads with analysis and reasons |
| GET | `/orders` | order drafts created by the agent |
| GET | `/metrics` | backend, model, hardware, latency, tok/s, fallbacks |
| GET | `/healthz`, `/version` | |

## Demo script
See `scripts/demo.sh` and `docs/video-script.md`.

## License
MIT — see `LICENSE`.
