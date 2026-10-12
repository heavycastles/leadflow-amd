"""LLM layer: OpenAI-compatible chat client (vLLM on ROCm / AMD Instinct MI300X) with a mock fallback.

The production path is a vLLM server started with the ROCm image on AMD Developer Cloud
(see deploy/vllm-rocm.sh). Anything that speaks `/v1/chat/completions` works, so the same
code runs against AMD hardware, a local vLLM, or the offline mock used in tests.
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field

import httpx

SYSTEM_PROMPT = """You are a sales & order assistant for a small online shop in Central Asia.
Customers write in Russian, Uzbek or English via Telegram, WhatsApp or the web.
Return ONLY a JSON object with keys:
 intent: one of ["order","quote","question","complaint","spam","other"],
 language: "ru" | "uz" | "en",
 products: list of {"name": str, "qty": int|null},
 budget: number|null, currency: str|null,
 urgency: "high" | "normal" | "low",
 reply: a short polite reply to the customer in THEIR language,
 next_action: one of ["create_order_draft","send_quote","call_back","answer_question","escalate","ignore"],
 rationale: one sentence explaining the classification.
"""


@dataclass
class LLMResult:
    data: dict
    backend: str
    model: str
    latency_ms: float
    prompt_tokens: int = 0
    completion_tokens: int = 0
    fallback_reason: str | None = None
    extra: dict = field(default_factory=dict)

    @property
    def tokens_per_sec(self) -> float:
        if not self.completion_tokens or not self.latency_ms:
            return 0.0
        return round(self.completion_tokens / (self.latency_ms / 1000), 1)


def _settings() -> dict:
    return {
        "backend": os.getenv("LLM_BACKEND", "mock").lower(),
        "base_url": os.getenv("LLM_BASE_URL", "http://localhost:8000/v1").rstrip("/"),
        "model": os.getenv("LLM_MODEL", "Qwen/Qwen2.5-7B-Instruct"),
        "api_key": os.getenv("LLM_API_KEY", "EMPTY"),
        "timeout": float(os.getenv("LLM_TIMEOUT", "30")),
        "fallback": os.getenv("LLM_FALLBACK", "1") not in {"0", "false", "no"},
        "hardware": os.getenv("LLM_HARDWARE", "AMD Instinct MI300X (ROCm, vLLM)"),
    }


def extract_json(text: str) -> dict:
    """Parse the first JSON object in a model response (tolerates ```json fences and chatter)."""
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        raise ValueError("no JSON object in model output")
    return json.loads(match.group(0))


# ---------------------------------------------------------------- mock backend
_ORDER = ("order", "buy", "закаж", "заказ", "куп", "возьму", "olaman", "buyurtma", "sotib")
_QUOTE = ("price", "quote", "cost", "цена", "сколько", "стоим", "narx", "qancha")
_COMPLAINT = ("broken", "refund", "сломан", "возврат", "жалоб", "brak", "qaytar")
_SPAM = ("casino", "crypto bonus", "казино", "click here")
_URGENT = ("urgent", "today", "asap", "срочно", "сегодня", "bugun", "tez")
_UZ = ("salom", "narx", "qancha", "kerak", "bugun", "olaman", "buyurtma", "rahmat")
_QTY = re.compile(r"(\d+)\s*(?:шт|pcs|x|dona|штук|units?)?\s+([A-Za-zА-Яа-яЁёʻ'\-]{3,})", re.U)
_NOT_PRODUCT = {"размера", "размер", "size", "сум", "sum", "som", "руб", "usd", "dollars", "years", "лет",
                "минут", "minutes", "часов", "hours", "days", "дней"}
_BUDGET = re.compile(r"(\d[\d\s]{1,12})\s*(\$|usd|сум|so'?m|sum|руб|rub)", re.I | re.U)
_REPLIES = {
    "ru": {"order": "Спасибо за заказ! Подготовили черновик, менеджер подтвердит наличие и доставку.",
           "quote": "Спасибо! Отправим цену и сроки в течение 15 минут.",
           "complaint": "Очень жаль! Передали менеджеру, он свяжется с вами сегодня.",
           "default": "Спасибо за сообщение! Скоро ответим."},
    "uz": {"order": "Buyurtma uchun rahmat! Menejer mavjudligini va yetkazishni tasdiqlaydi.",
           "quote": "Rahmat! Narx va muddatni 15 daqiqada yuboramiz.",
           "complaint": "Uzr so'raymiz! Menejer bugun siz bilan bog'lanadi.",
           "default": "Xabaringiz uchun rahmat! Tez orada javob beramiz."},
    "en": {"order": "Thanks for your order! We drafted it; a manager will confirm stock and delivery.",
           "quote": "Thanks! We'll send the price and lead time within 15 minutes.",
           "complaint": "Sorry about that! A manager will contact you today.",
           "default": "Thanks for your message! We'll reply shortly."},
}
_NEXT = {"order": "create_order_draft", "quote": "send_quote", "complaint": "escalate",
         "spam": "ignore", "question": "answer_question", "other": "call_back"}


def mock_analyze(message: str) -> dict:
    """Deterministic, offline stand-in for the model. Used in tests and as GPU-less fallback."""
    text = (message or "").lower()
    if re.search(r"[а-яё]", text):
        lang = "uz" if any(w in text for w in _UZ) else "ru"
    else:
        lang = "uz" if any(w in text for w in _UZ) else "en"
    if any(w in text for w in _SPAM):
        intent = "spam"
    elif any(w in text for w in _COMPLAINT):
        intent = "complaint"
    elif any(w in text for w in _ORDER):
        intent = "order"
    elif any(w in text for w in _QUOTE):
        intent = "quote"
    elif "?" in text:
        intent = "question"
    else:
        intent = "other"
    products = [
        {"name": m.group(2), "qty": int(m.group(1))}
        for m in _QTY.finditer(message or "")
        if int(m.group(1)) <= 1000 and m.group(2).lower() not in _NOT_PRODUCT
    ]
    budget = currency = None
    if b := _BUDGET.search(message or ""):
        budget = float(re.sub(r"\s", "", b.group(1)))
        cur = b.group(2).lower()
        currency = "USD" if cur in {"$", "usd"} else "RUB" if cur in {"руб", "rub"} else "UZS"
    urgency = "high" if any(w in text for w in _URGENT) else "normal"
    reply = _REPLIES[lang].get(intent, _REPLIES[lang]["default"])
    return {
        "intent": intent, "language": lang, "products": products, "budget": budget,
        "currency": currency, "urgency": urgency, "reply": reply, "next_action": _NEXT[intent],
        "rationale": f"keyword rules matched intent={intent}, urgency={urgency}",
    }


# ---------------------------------------------------------------- client
class LLMClient:
    def __init__(self, transport: httpx.BaseTransport | None = None) -> None:
        self.cfg = _settings()
        self._transport = transport

    @property
    def info(self) -> dict:
        return {k: self.cfg[k] for k in ("backend", "base_url", "model", "hardware", "fallback")}

    def analyze(self, message: str) -> LLMResult:
        if self.cfg["backend"] == "mock":
            return self._mock(message)
        try:
            return self._remote(message)
        except Exception as exc:  # noqa: BLE001 - any remote failure may fall back
            if not self.cfg["fallback"]:
                raise
            return self._mock(message, fallback_reason=f"{type(exc).__name__}: {exc}"[:200])

    def _mock(self, message: str, fallback_reason: str | None = None) -> LLMResult:
        t0 = time.perf_counter()
        data = mock_analyze(message)
        return LLMResult(data=data, backend="mock", model="rules-v1",
                         latency_ms=round((time.perf_counter() - t0) * 1000, 2),
                         fallback_reason=fallback_reason)

    def _remote(self, message: str) -> LLMResult:
        cfg = self.cfg
        body = {
            "model": cfg["model"],
            "temperature": 0.1,
            "max_tokens": 400,
            "response_format": {"type": "json_object"},
            "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                         {"role": "user", "content": message}],
        }
        t0 = time.perf_counter()
        with httpx.Client(timeout=cfg["timeout"], transport=self._transport) as http:
            r = http.post(f"{cfg['base_url']}/chat/completions", json=body,
                          headers={"Authorization": f"Bearer {cfg['api_key']}"})
            r.raise_for_status()
            payload = r.json()
        latency = (time.perf_counter() - t0) * 1000
        data = extract_json(payload["choices"][0]["message"]["content"])
        usage = payload.get("usage") or {}
        return LLMResult(data=data, backend="openai", model=payload.get("model", cfg["model"]),
                         latency_ms=round(latency, 1),
                         prompt_tokens=usage.get("prompt_tokens", 0),
                         completion_tokens=usage.get("completion_tokens", 0),
                         extra={"hardware": cfg["hardware"]})
