"""LLM layer: OpenAI-compatible chat client (AMD Token Factory / vLLM on ROCm) with a mock fallback.

One-key live path: set AMD_TOKEN_FACTORY_API_KEY (or RADEON_API_KEY) and the client talks to the
AMD Token Factory public model API (https://developer.amd.com.cn/radeon/api/v1, OpenAI-compatible,
no card needed). Optional: a vLLM server started with the ROCm image on AMD Developer Cloud MI300X
(see deploy/vllm-rocm.sh) for real GPU benchmarks. Anything that speaks `/v1/chat/completions` works,
so the same code runs against AMD Token Factory, AMD hardware, a local vLLM, or the offline mock.

Resolution order (explicit LLM_* always wins; blank values count as unset):
  backend : LLM_BACKEND  >  "openai" if a Token Factory key is set  >  "mock"
  base_url: LLM_BASE_URL >  AMD_TOKEN_FACTORY_BASE_URL / TOKEN_FACTORY_BASE_URL (with key) > localhost vLLM
  api_key : LLM_API_KEY  >  AMD_TOKEN_FACTORY_API_KEY  >  RADEON_API_KEY  >  "EMPTY"
  model   : LLM_MODEL    >  AMD_TOKEN_FACTORY_MODEL (with key)  >  DEFAULT_TOKEN_FACTORY_MODEL / Qwen2.5-7B
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


TOKEN_FACTORY_BASE_URL = "https://developer.amd.com.cn/radeon/api/v1"  # noqa: S105 - not a secret
DEFAULT_TOKEN_FACTORY_MODEL = "Gemma-4-31B-IT"  # noqa: S105 - Google Gemma on AMD GPUs; alt: "DeepSeek-V4-Flash"
TOKEN_FACTORY_HARDWARE = "AMD Radeon Cloud GPUs (AMD Token Factory API)"  # noqa: S105 - not a secret
VLLM_BASE_URL = "http://localhost:8000/v1"
VLLM_MODEL = "Qwen/Qwen2.5-7B-Instruct"
VLLM_HARDWARE = "AMD Instinct MI300X (ROCm, vLLM)"


def _env(name: str, default: str = "") -> str:
    """Env var, treating unset *and* blank (e.g. `LLM_BASE_URL=` copied from .env.example) as default."""
    v = os.getenv(name, "").strip()
    return v or default


def token_factory_key() -> str:
    return _env("AMD_TOKEN_FACTORY_API_KEY") or _env("RADEON_API_KEY")


def _settings() -> dict:
    tf_key = token_factory_key()
    backend = _env("LLM_BACKEND", "openai" if tf_key else "mock").lower()
    explicit_url = _env("LLM_BASE_URL")
    tf_url = _env("AMD_TOKEN_FACTORY_BASE_URL") or _env("TOKEN_FACTORY_BASE_URL") or TOKEN_FACTORY_BASE_URL
    # Token Factory is the target when a key is present and no explicit LLM_BASE_URL points elsewhere.
    use_tf = bool(tf_key) and not explicit_url
    base_url = explicit_url or (tf_url if tf_key else VLLM_BASE_URL)
    model = _env("LLM_MODEL") or (
        _env("AMD_TOKEN_FACTORY_MODEL", DEFAULT_TOKEN_FACTORY_MODEL) if use_tf else VLLM_MODEL)
    return {
        "backend": backend,
        "provider": "amd-token-factory" if use_tf and backend != "mock" else (
            "mock" if backend == "mock" else "openai-compatible"),
        "base_url": base_url.rstrip("/"),
        "model": model,
        "api_key": _env("LLM_API_KEY") or tf_key or "EMPTY",
        "timeout": float(_env("LLM_TIMEOUT", "30")),
        "fallback": _env("LLM_FALLBACK", "1").lower() not in {"0", "false", "no"},
        # Some Token Factory models ignore/refuse response_format; LLM_JSON_MODE=0 drops it
        # (extract_json() still tolerates chatter around the JSON object).
        "json_mode": _env("LLM_JSON_MODE", "1").lower() not in {"0", "false", "no"},
        "hardware": _env("LLM_HARDWARE", TOKEN_FACTORY_HARDWARE if use_tf else VLLM_HARDWARE),
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
_UZ = ("salom", "narx", "qancha", "kerak", "bugun", "olaman", "buyurtma", "rahmat", "qaytar", "keldi", "pulni",
       "dona")
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
        return {k: self.cfg[k] for k in ("backend", "provider", "base_url", "model", "hardware", "fallback")}

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
            "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                         {"role": "user", "content": message}],
        }
        if cfg["json_mode"]:
            body["response_format"] = {"type": "json_object"}
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
                         extra={"hardware": cfg["hardware"], "provider": cfg["provider"]})


def check(transport: httpx.BaseTransport | None = None) -> dict:
    """Live smoke check: list models, confirm the configured one exists, run one tiny analysis.

    `python -m app.llm` — needs AMD_TOKEN_FACTORY_API_KEY (or RADEON_API_KEY / LLM_* for vLLM).
    Never prints the key.
    """
    cfg = _settings()
    out: dict = {"backend": cfg["backend"], "provider": cfg["provider"], "base_url": cfg["base_url"],
                 "model": cfg["model"], "key_set": cfg["api_key"] != "EMPTY"}
    if cfg["backend"] == "mock":
        return {**out, "ok": False,
                "error": "backend is mock (set AMD_TOKEN_FACTORY_API_KEY or LLM_BACKEND=openai)"}
    headers = {"Authorization": f"Bearer {cfg['api_key']}"}
    try:
        with httpx.Client(timeout=cfg["timeout"], transport=transport) as http:
            r = http.get(f"{cfg['base_url']}/models", headers=headers)
            r.raise_for_status()
            payload = r.json()
        items = payload.get("data", []) if isinstance(payload, dict) else payload
        ids = sorted({m.get("id") for m in items if isinstance(m, dict) and m.get("id")})
        out["models"] = ids
        out["model_available"] = cfg["model"] in ids
    except Exception as exc:  # noqa: BLE001
        return {**out, "ok": False, "error": f"list models: {type(exc).__name__}: {exc}"[:200]}
    client = LLMClient(transport=transport)
    client.cfg["fallback"] = False
    try:
        res = client.analyze("Salom! 2 dona choynak kerak, narxi qancha?")
        out["sample"] = {"intent": res.data.get("intent"), "language": res.data.get("language"),
                         "latency_ms": res.latency_ms, "completion_tokens": res.completion_tokens}
    except Exception as exc:  # noqa: BLE001
        return {**out, "ok": False, "error": f"chat: {type(exc).__name__}: {exc}"[:200]}
    out["ok"] = True
    return out


if __name__ == "__main__":  # python -m app.llm -> live config check
    print(json.dumps(check(), indent=2, ensure_ascii=False))
