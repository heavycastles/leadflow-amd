# Slide deck outline (8–10 slides)

1. **Title** — LeadFlow AI: multilingual commerce lead & order agent on AMD MI300X. Name, track, logo/cover.
2. **Problem** — SMB shops in Central Asia sell via Telegram/WhatsApp; 3 languages, dozens of messages/day,
   slow replies = lost buyers. One stat/quote + screenshot of a messy chat.
3. **Solution** — agent reads every message, extracts the order, replies in the customer's language, ranks leads,
   drafts orders. One-line flow diagram.
4. **Live demo screenshot** — dashboard: ranked leads, reasons, reply drafts, order drafts, tok/s panel.
5. **Architecture** — Telegram → n8n → FastAPI → CommerceAgent → vLLM on MI300X (ROCm); fallback path.
6. **Why AMD** — MI300X 192 GB HBM3: one GPU serves many tenants / bigger models; ROCm + vLLM drop-in
   OpenAI-compatible API; benchmark table (req/s, tok/s, latency, accuracy) from scripts/benchmark.py.
7. **Trust & explainability** — hybrid score with reasons, strict JSON validation, graceful degradation.
8. **Business value** — SaaS per shop/month; time saved per message; conversion uplift hypothesis; market (UZ/KZ
   e-commerce via messengers).
9. **Roadmap** — WhatsApp Business API, catalog/stock lookup (RAG), payments (Click/Payme), fine-tuned UZ model on MI300X.
10. **Team & links** — heavycastles, GitHub, demo URL.
