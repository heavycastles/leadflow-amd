# lablab.ai — paste-ready submit pack (AMD ACT III / LeadFlow AI)

Copy fields into the lablab submission form. Repo is public, video is on YouTube (unlisted), live AMD Token Factory
mode is verified (see `docs/live-proof.md`). Show the filled form to the owner before pressing Submit.
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

## Links

| Field | Value |
|-------|--------|
| GitHub repo | https://github.com/heavycastles/leadflow-amd |
| Demo app URL | optional — leave blank unless a Render deploy from `render.yaml` is approved |
| Video URL | https://youtu.be/KZSxeaZ0K50 |
| Slides | upload local file `docs/slides.pdf` |
| Cover image | upload local file `docs/cover.png` |

## Local asset paths (on this machine)

| Asset | Path |
|-------|------|
| Demo video (latest) | `amd-act-iii/docs/demo-v6.mp4` |
| Demo v2 / draft | `amd-act-iii/docs/demo-v2.mp4` |
| Slides PDF | `amd-act-iii/docs/slides.pdf` |
| Cover | `amd-act-iii/docs/cover.png` |
| Video script | `amd-act-iii/docs/video-script.md` |
| Narration | `amd-act-iii/docs/video-narration.txt` |
| Mock benchmarks note | `amd-act-iii/docs/benchmarks-mock.md` (NOT live GPU numbers) |
| Live Token Factory proof | `amd-act-iii/docs/live-proof.md`, `docs/live-proof-*.png`, `docs/live-benchmark-tokenfactory.json` |

## Checklist (status 2026-10-18)

- [x] Discord connected on lablab.ai, team created for AMD ACT III
- [x] Public repo https://github.com/heavycastles/leadflow-amd (MIT, CI green, 30 tests)
- [x] Demo video on YouTube: https://youtu.be/KZSxeaZ0K50 (channel "Builds Lab")
- [x] AMD Token Factory key received; live mode verified with `DeepSeek-V4-Flash` (0 fallbacks) — `docs/live-proof.md`
- [x] Slides `docs/slides.pdf` and cover `docs/cover.png` ready
- [ ] Sign in to lablab (AMD SSO), fill the form with the fields above, owner reviews
- [ ] Press Submit by **18 Oct 2026 18:00 MSK** (aim for 14:00)
- [ ] Optional: Render live demo URL

Hackathon page: https://lablab.ai/ai-hackathons/amd-developer-hackathon-act-iii

**Never paste API keys into the form or the repo.**
