# lablab.ai — paste-ready submit pack (AMD ACT III / LeadFlow AI)

Copy fields into the lablab submission form once Discord + public repo + demo review are done.
**Do not invent live URLs** — leave GitHub / demo as TODO until user approves publish + deploy.
Deadline: **18 Oct 2026, 18:00 MSK**.

Source of truth: `../SUBMISSION.md` (keep in sync if that file changes).

---

## Title
```
LeadFlow AI — multilingual commerce lead & order agent on AMD GPUs
```

## Short description (≤255 chars)
```
An AI sales agent for small shops: reads Telegram/WhatsApp/web messages in RU/UZ/EN, extracts orders, drafts replies
and ranks leads with an explainable score — powered by open LLMs on AMD GPUs via AMD Token Factory.
```

## Long description
```
Small online shops in Central Asia sell through chat. Owners drown in mixed-language messages and lose hot buyers
while answering price questions. LeadFlow AI is an agent that sits between the shop's channels and its owner.

Every incoming message goes through an open LLM served on AMD GPUs through the AMD Token Factory API
(OpenAI-compatible, DeepSeek-V4-Flash by default — one API key switches the app live). The same client also runs
against a self-hosted vLLM on an AMD Instinct MI300X with ROCm (Qwen2.5-7B-Instruct) for dedicated deployments. The agent classifies intent (order, quote, question, complaint, spam),
extracts products, quantities, budget and urgency, writes a reply in the customer's own language, and when the
customer wants to buy, creates an order draft automatically.

Leads are ranked by a hybrid score: deterministic rules (contact quality, channel, keywords, de-duplication) plus
model-extracted features, with a human-readable reason for every point. Model output is strictly validated, and
if the LLM endpoint fails the system degrades to an offline analyzer instead of going down.

An n8n workflow connects a Telegram shop bot: customer writes → agent analyzes on AMD → reply sent → owner gets a
ping for hot leads. A dashboard shows ranked leads, order drafts and live inference metrics (latency, tokens/s).

Because the MI300X has 192 GB of memory, one GPU can serve many shops concurrently, or a much larger model
without sharding — a cheap path to a multi-tenant SaaS for SMB commerce.
```

## Track
```
Reinvent Commerce
```

## Tech tags
```
AMD Token Factory, AMD Instinct MI300X, AMD Developer Cloud, ROCm, vLLM, DeepSeek, Qwen2.5, FastAPI, Python, n8n, Telegram, AI Agents, LLM, E-commerce
```

## Links (paste when ready — TODOs until user OK)

| Field | Value |
|-------|--------|
| GitHub repo | **TODO** — `heavycastles/leadflow-amd` (after user «ОК, публикуй»; local: `scripts/publish_github.sh`) |
| Demo app URL | **TODO** — Render Blueprint from `render.yaml` (after user Render account + deploy OK) |
| Video URL | **TODO** — upload `docs/demo-v3.mp4` after user review (YouTube/Drive as form requires) |
| Slides | upload local file `docs/slides.pdf` |
| Cover image | upload local file `docs/cover.png` |

## Local asset paths (on this machine)

| Asset | Path |
|-------|------|
| Demo video (latest) | `amd-act-iii/docs/demo-v3.mp4` |
| Demo v2 / draft | `amd-act-iii/docs/demo-v2.mp4` |
| Slides PDF | `amd-act-iii/docs/slides.pdf` |
| Cover | `amd-act-iii/docs/cover.png` |
| Video script | `amd-act-iii/docs/video-script.md` |
| Narration | `amd-act-iii/docs/video-narration.txt` |
| Mock benchmarks note | `amd-act-iii/docs/benchmarks-mock.md` (NOT live GPU numbers) |

## Remaining user checklist (must finish before Submit)

1. Connect Discord on lablab.ai for AMD ACT III (unread Action Required from no-reply@lablab.ai, 13 & 15 Oct).
2. AMD Token Factory key at https://notebooks.amd.com/tokenfactory (no card) → paste/`./scripts/go_live.sh rc-...`.
3. Approve public GitHub repo `heavycastles/leadflow-amd`.
4. Approve Render demo deploy; paste live URL into Links.
5. Review `docs/demo-v3.mp4` (upload for the form if required).
6. Hit Submit on lablab by **18 Oct 2026 18:00 MSK**.

Hackathon page: https://lablab.ai/ai-hackathons/amd-developer-hackathon-act-iii

**Do not push, submit, or invent live URLs / API keys / live benchmark numbers from this pack alone.**
