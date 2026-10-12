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

**Links (TODO):** GitHub repo · demo app URL · video · slides PDF · cover image
