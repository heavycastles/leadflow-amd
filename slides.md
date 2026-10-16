---
marp: true
theme: default
paginate: true
size: 16:9
style: |
  section { font-family: Inter, Helvetica, Arial, sans-serif; }
  h1 { color: #ed1c24; }
  h2 { color: #1a1a1a; }
  footer { color: #666; font-size: 14px; }
  table { font-size: 18px; }
  code { background: #f4f4f4; }
footer: LeadFlow AI · AMD Developer Hackathon ACT III · MIT
---

<!-- _class: lead -->
# LeadFlow AI
## Multilingual commerce lead & order agent on AMD GPUs (Token Factory · MI300X-ready)

**heavycastles** · Track: Reinvent Commerce  
lablab.ai AMD Developer Hackathon: ACT III

---

# Problem

SMB shops in Central Asia sell via **Telegram / WhatsApp**.

- 3 languages (RU / UZ / EN) mixed in one inbox
- Dozens of messages per day
- Slow replies = lost buyers

> One missed “хочу купить” at peak hour costs a sale.

---

# Solution

An agent that sits between the shop’s channels and the owner:

1. **Reads** every incoming message
2. **Extracts** intent, products, quantities, budget, urgency
3. **Replies** in the customer’s language
4. **Ranks** leads with an explainable hybrid score
5. **Drafts** orders when the buyer is ready

```
message → n8n → FastAPI → CommerceAgent → AMD Token Factory (or vLLM@MI300X) → reply + score
```

---

# Live demo (dashboard)

Ranked leads · reasons · reply drafts · order drafts · tok/s panel

- Hot lead ping to the shop owner
- FALLBACK badge when GPU is unreachable
- Metrics: latency, aggregate tok/s, backend, fallbacks

*(Recorded demo / screenshots go in the submission video.)*

---

# Architecture

```
Telegram / WhatsApp / Web
        │  n8n workflow
        ▼
FastAPI  POST /leads → LeadStore → CommerceAgent
                                      ├─ LLMClient → AMD Token Factory | vLLM on MI300X (ROCm)
                                      ├─ sanitize() strict JSON
                                      ├─ hybrid_score() + reasons
                                      └─ order drafts
        ▼
Dashboard  /leads · /orders · /metrics
```

Graceful degradation: offline analyzer if the GPU endpoint fails.

---

# Why AMD

| Layer | Choice |
|---|---|
| Live API | **AMD Token Factory** (AMD GPUs, OpenAI-compatible, one key) — DeepSeek-V4-Flash |
| Self-hosted | AMD Instinct **MI300X** (192 GB HBM3) · **ROCm** + `rocm/vllm` · Qwen2.5-7B (70B-class fits) |
| Workload | intent · entities · multilingual reply drafting |

**Live on AMD Token Factory (one key). Optional self-hosted MI300X benchmark — TBD if credits are used:**

| model | conc. | req/s | tok/s | latency | intent acc. |
|---|---|---|---|---|---|
| Qwen2.5-7B-Instruct (MI300X) | 8 | **TBD** | **TBD** | **TBD** | **TBD** |

---

# Trust & explainability

- **Hybrid score** = deterministic rules + model features
- Every point has a **human-readable reason**
- Model JSON is **strictly validated** and clamped
- No LLM-only decisions; degrades instead of lying

---

# Business value

- SaaS: per shop / month
- Time saved per message; conversion uplift hypothesis
- Market: UZ / KZ e-commerce via messengers
- One MI300X → many tenants or a larger model (no sharding)

---

# Roadmap

1. WhatsApp Business API
2. Catalog / stock lookup (RAG)
3. Payments (Click / Payme)
4. Fine-tuned Uzbek model on MI300X

---

# Team & links

**heavycastles**

- GitHub: `github.com/heavycastles/leadflow-amd`
- Demo URL: *(TODO)*
- Video · slides PDF · cover: see `docs/`

MIT licensed · Built for AMD Developer Hackathon ACT III
