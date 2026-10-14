# lablab.ai submission draft — AMD Developer Hackathon: ACT III

**Title:** LeadFlow AI — multilingual commerce lead & order agent on AMD MI300X

**Short description (≤255 chars):**
An AI sales agent for small shops: reads Telegram/WhatsApp/web messages in RU/UZ/EN, extracts orders, drafts replies
and ranks leads with an explainable score — powered by vLLM on AMD Instinct MI300X.

**Long description:**
Small online shops in Central Asia sell through chat. Owners drown in mixed-language messages and lose hot buyers
while answering price questions. LeadFlow AI is an agent that sits between the shop's channels and its owner.

Every incoming message goes through an open LLM (Qwen2.5-7B-Instruct) served with vLLM on an AMD Instinct MI300X
GPU on AMD Developer Cloud with ROCm. The agent classifies intent (order, quote, question, complaint, spam),
extracts products, quantities, budget and urgency, writes a reply in the customer's own language, and when the
customer wants to buy, creates an order draft automatically.

Leads are ranked by a hybrid score: deterministic rules (contact quality, channel, keywords, de-duplication) plus
model-extracted features, with a human-readable reason for every point. Model output is strictly validated, and
if the GPU endpoint fails the system degrades to an offline analyzer instead of going down.

An n8n workflow connects a Telegram shop bot: customer writes → agent analyzes on AMD → reply sent → owner gets a
ping for hot leads. A dashboard shows ranked leads, order drafts and live inference metrics (latency, tokens/s).

Because the MI300X has 192 GB of memory, one GPU can serve many shops concurrently, or a much larger model
without sharding — a cheap path to a multi-tenant SaaS for SMB commerce.

**Tech tags:** AMD Instinct MI300X, AMD Developer Cloud, ROCm, vLLM, Qwen2.5, FastAPI, Python, n8n, Telegram,
AI Agents, LLM, E-commerce

**Track:** Reinvent Commerce

**Links:**
- GitHub repo: TODO — `heavycastles/leadflow-amd` (use `scripts/publish_github.sh` when `gh` is logged in)
- Demo app URL: TODO
- Video: latest draft `docs/demo-v3.mp4` (also `demo-v2.mp4` / `demo-draft.mp4`; still needs MI300X benchmark segment and user review; script in `docs/video-script.md`, narration in `docs/video-narration.txt`)
- Slides PDF: `docs/slides.pdf` (local; upload on submit)
- Cover image: `docs/cover.png` (local; upload on submit)

**Remaining before submit (user):**
1. Connect Discord on lablab.ai for AMD ACT III.
2. Sign in at [login.amd.com](https://login.amd.com), then claim $100 AMD Developer Cloud credits at [developer.amd.com/ai-developer-program](https://developer.amd.com/ai-developer-program/) (needed for MI300X benchmarks).
3. Approve creating/publishing public GitHub repo `heavycastles/leadflow-amd` (local pack is ready; push when approved).
4. Approve demo deploy via Render Blueprint (`render.yaml` → free tier, mock LLM) and paste the live URL into Links above.
5. Review `docs/demo-v3.mp4` (upload to YouTube/Drive for the form if required).
6. Submit on lablab.ai by **Oct 18, 2026 18:00 MSK**.
