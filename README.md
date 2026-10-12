# LeadFlow AI — commerce lead & order agent on AMD

Small shops in Central Asia get dozens of messages a day in Russian, Uzbek and English from Telegram, WhatsApp
and the web. LeadFlow AI reads every message with an open LLM served by **vLLM on an AMD Instinct MI300X (ROCm)**,
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
        │                   ├─ LLMClient ──► OpenAI-compatible /v1/chat/completions
        │                   │                 = vLLM on AMD Instinct MI300X (ROCm)   app/llm.py
        │                   │                 (mock fallback when GPU is unreachable)
        │                   ├─ sanitize()   strict validation of model JSON
        │                   ├─ hybrid_score() rules + model features + reasons
        │                   └─ order drafts
        ▼
Web dashboard (/)  · /leads · /orders · /metrics (latency, tok/s, backend, fallbacks)
```

Design choices:
- **LLM is pluggable via env** (`LLM_BACKEND`, `LLM_BASE_URL`, `LLM_MODEL`, `LLM_API_KEY`). Any OpenAI-compatible
  server works; the reference deployment is vLLM on AMD Developer Cloud.
- **No LLM-only decisions**: model output is validated and clamped, and the score always shows *why*.
- **Graceful degradation**: if the GPU endpoint is down, a deterministic offline analyzer answers and the UI
  marks the result as FALLBACK (disable with `LLM_FALLBACK=0`).

## AMD usage

| Layer | AMD technology |
|---|---|
| Inference hardware | AMD Instinct **MI300X** (192 GB HBM3) on **AMD Developer Cloud** |
| Software stack | **ROCm** + `rocm/vllm` container, OpenAI-compatible server |
| Model | `Qwen/Qwen2.5-7B-Instruct` (default; any HF instruct model fits in MI300X memory, incl. 70B-class) |
| What runs on AMD | every lead analysis: intent classification, entity extraction, multilingual reply drafting |
| Measured | `scripts/benchmark.py` — latency, aggregate tok/s under concurrency, JSON validity, intent accuracy |

Benchmark results on MI300X: **TODO — fill in after running on AMD Developer Cloud.**

| model | concurrency | req/s | aggregate tok/s | avg latency | intent accuracy |
|---|---|---|---|---|---|
| Qwen2.5-7B-Instruct | 8 | TBD | TBD | TBD | TBD |

## Setup

### 1. Local (no GPU, mock LLM)
```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
python serve.py            # http://localhost:8080
./scripts/demo.sh          # feeds 5 multilingual sample leads
```

### 2. vLLM on AMD Developer Cloud (MI300X)
```bash
# on the GPU droplet (ROCm image)
export HF_TOKEN=...           # if the model is gated
./deploy/vllm-rocm.sh         # serves http://<droplet-ip>:8000/v1
```
Then point the app at it:
```bash
cp .env.example .env
# LLM_BACKEND=openai
# LLM_BASE_URL=http://<droplet-ip>:8000/v1
python serve.py
LLM_BACKEND=openai LLM_BASE_URL=http://<droplet-ip>:8000/v1 python -m scripts.benchmark --concurrency 8
```
Tip: run the app on the same droplet and keep port 8000 firewalled, or start vLLM with `VLLM_API_KEY`.

### 3. docker-compose (app + n8n)
```bash
docker compose up --build                    # app :8080, n8n :5678
docker compose --profile amd up --build      # also starts vLLM on the local AMD GPU
```
In n8n: import `n8n/telegram-leadflow.json`, add Telegram credentials, set `OWNER_CHAT_ID`, activate.

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
