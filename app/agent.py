"""Commerce agent: LLM extraction + deterministic rules -> explainable hybrid score and next action."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from itertools import count

from app.leads import Lead
from app.llm import LLMClient, LLMResult

INTENTS = {"order", "quote", "question", "complaint", "spam", "other"}
ACTIONS = {"create_order_draft", "send_quote", "call_back", "answer_question", "escalate", "ignore"}
_INTENT_POINTS = {"order": 25, "quote": 15, "question": 5, "complaint": 0, "other": 0, "spam": -60}


def sanitize(data: dict) -> dict:
    """Validate/clamp model output so a hallucinated field can never break the pipeline."""
    intent = data.get("intent") if data.get("intent") in INTENTS else "other"
    action = data.get("next_action") if data.get("next_action") in ACTIONS else "call_back"
    products = []
    for p in data.get("products") or []:
        if isinstance(p, dict) and p.get("name"):
            qty = p.get("qty")
            products.append({"name": str(p["name"])[:80],
                             "qty": int(qty) if isinstance(qty, (int, float)) and qty > 0 else None})
    budget = data.get("budget")
    budget = float(budget) if isinstance(budget, (int, float)) and budget > 0 else None
    return {
        "intent": intent,
        "language": data.get("language") if data.get("language") in {"ru", "uz", "en"} else "en",
        "products": products[:10],
        "budget": budget,
        "currency": (str(data.get("currency"))[:8] if data.get("currency") else None),
        "urgency": data.get("urgency") if data.get("urgency") in {"high", "normal", "low"} else "normal",
        "reply": str(data.get("reply") or "")[:1000],
        "next_action": action,
        "rationale": str(data.get("rationale") or "")[:300],
    }


def hybrid_score(rule_score: int, a: dict) -> tuple[int, list[str]]:
    """Rule score + model features. Returns score and human-readable reasons (no black box)."""
    reasons = [f"rule score {rule_score} (contacts, source, keywords)"]
    score = rule_score
    pts = _INTENT_POINTS[a["intent"]]
    if pts:
        score += pts
        reasons.append(f"intent={a['intent']} {pts:+d}")
    if a["products"]:
        score += 10
        reasons.append(f"{len(a['products'])} product(s) identified +10")
    if a["budget"]:
        score += 10
        reasons.append("budget stated +10")
    if a["urgency"] == "high":
        score += 10
        reasons.append("urgent +10")
    return max(0, min(100, score)), reasons


@dataclass
class OrderDraft:
    id: int
    lead_id: int
    items: list
    budget: float | None
    currency: str | None
    status: str = "draft"


@dataclass
class Analysis:
    lead_id: int
    analysis: dict
    hybrid_score: int
    reasons: list[str]
    llm: dict
    order_draft: dict | None = None
    notes: list[str] = field(default_factory=list)


class CommerceAgent:
    def __init__(self, llm: LLMClient | None = None) -> None:
        self.llm = llm or LLMClient()
        self.orders: dict[int, OrderDraft] = {}
        self._order_ids = count(1)
        self.analyses: dict[int, Analysis] = {}
        self.stats = {"calls": 0, "completion_tokens": 0, "total_ms": 0.0, "fallbacks": 0}

    def process(self, lead: Lead) -> Analysis:
        res: LLMResult = self.llm.analyze(lead.message or "")
        a = sanitize(res.data)
        score, reasons = hybrid_score(lead.score, a)
        self.stats["calls"] += 1
        self.stats["completion_tokens"] += res.completion_tokens
        self.stats["total_ms"] += res.latency_ms
        if res.fallback_reason:
            self.stats["fallbacks"] += 1
        draft = None
        if a["next_action"] == "create_order_draft" and a["products"]:
            od = OrderDraft(id=next(self._order_ids), lead_id=lead.id, items=a["products"],
                            budget=a["budget"], currency=a["currency"])
            self.orders[od.id] = od
            draft = asdict(od)
        result = Analysis(
            lead_id=lead.id, analysis=a, hybrid_score=score, reasons=reasons, order_draft=draft,
            llm={"backend": res.backend, "model": res.model, "latency_ms": res.latency_ms,
                 "completion_tokens": res.completion_tokens, "tokens_per_sec": res.tokens_per_sec,
                 "fallback_reason": res.fallback_reason, **res.extra},
        )
        self.analyses[lead.id] = result
        return result

    def metrics(self) -> dict:
        s = self.stats
        tps = s["completion_tokens"] / (s["total_ms"] / 1000) if s["total_ms"] else 0.0
        return {**s, "avg_latency_ms": round(s["total_ms"] / s["calls"], 1) if s["calls"] else 0.0,
                "avg_tokens_per_sec": round(tps, 1), "llm": self.llm.info}
