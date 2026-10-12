# Demo video script (2:30)

**0:00–0:15 Hook.** (Face or title card) "Small shops in Uzbekistan sell through Telegram — in three languages.
Every slow reply is a lost sale. This is LeadFlow AI, running on an AMD Instinct MI300X."

**0:15–0:40 Problem.** Show a phone chat with mixed RU/UZ/EN messages. "Orders, price questions, complaints and
spam all land in one inbox."

**0:40–1:30 Live demo.** Screen: dashboard.
- Type the Uzbek message "Salom! 3 dona kurtka kerak, bugun olaman. Narxi qancha?" → Analyze.
- Point at: intent, language=uz, product 3× kurtka, urgency high, reply drafted in Uzbek, order draft created.
- Click "Load demo leads": Russian order jumps to the top (score 100), English quote next, complaint escalated,
  spam drops to 0. Hover the reasons line: "every point is explained."
- Optional: Telegram bot — send a message from phone, bot replies, owner gets 🔥 hot-lead ping (n8n).

**1:30–2:05 AMD.** Terminal on AMD Developer Cloud: `rocm-smi` showing MI300X, `deploy/vllm-rocm.sh` log,
then `python -m scripts.benchmark --concurrency 8` output. "Every analysis runs on vLLM on ROCm. X requests/s,
Y tokens/s aggregate on a single MI300X; 192 GB means one GPU can serve hundreds of shops."
Show dashboard metrics panel: backend=openai, hardware=MI300X, latency, tok/s.

**2:05–2:30 Close.** Architecture slide → business model → "LeadFlow AI: never miss a buyer. Open source, MIT,
link in description."
