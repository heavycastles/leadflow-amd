# lablab.ai submission draft — AMD Developer Hackathon: ACT III

**Title:** LeadFlow AI — multilingual commerce lead & order agent on AMD GPUs

**Short description (≤255 chars):**
An AI sales agent for small shops: reads Telegram/WhatsApp/web messages in RU/UZ/EN, extracts orders, drafts replies
and ranks leads with an explainable score — powered by open LLMs on AMD GPUs via AMD Token Factory.

**Long description:**
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

**Tech tags:** AMD Token Factory, AMD Instinct MI300X, AMD Developer Cloud, ROCm, vLLM, DeepSeek, Qwen2.5, FastAPI, Python, n8n, Telegram,
AI Agents, LLM, E-commerce

**Track:** Reinvent Commerce

**Links:**
- GitHub repo: https://github.com/heavycastles/leadflow-amd (public, MIT)
- Demo app URL: TODO
- Video: https://youtu.be/KZSxeaZ0K50 (`docs/demo-v6.mp4`; script in `docs/video-script.md`, narration in `docs/video-narration.txt`)
- Live proof (AMD Token Factory, DeepSeek-V4-Flash): `docs/live-proof.md`
- Slides PDF: `docs/slides.pdf` (local; upload on submit)
- Cover image: `docs/cover.png` (local; upload on submit)
- Local CI: `.github/workflows/ci.yml` (pytest on push/PR)
- Mock benchmark note: `docs/benchmarks-mock.md` (NOT GPU; live Token Factory check via `python -m app.llm`; MI300X numbers optional)

**Remaining before submit (user):**
1. Connect Discord on lablab.ai for AMD ACT III (Action Required emails from no-reply@lablab.ai).
2. Sign up for AMD Token Factory API at [notebooks.amd.com/tokenfactory](https://notebooks.amd.com/tokenfactory) — **no billing / credit card needed** — and run `./scripts/go_live.sh rc-...` (writes `.env` + verifies via `python -m app.llm`; the only setting needed). Per lablab FAQ (2026-10-15): developers do **not** need the $100 credit to participate; the Token Factory API is enough. Optional: claim $100 AMD Developer Cloud credits at [developer.amd.com/ai-developer-program](https://developer.amd.com/ai-developer-program/) only if you want real MI300X benchmarks (login.amd.com).
3. Approve creating/publishing public GitHub repo `heavycastles/leadflow-amd` (local pack is ready; push when approved).
4. Approve demo deploy via Render Blueprint (`render.yaml` → free tier, mock LLM) and paste the live URL into Links above.
5. Review `docs/demo-v6.mp4` (upload to YouTube/Drive for the form if required).
6. Submit on lablab.ai by **Oct 18, 2026 18:00 MSK**.
