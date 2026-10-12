from app.agent import CommerceAgent, hybrid_score, sanitize
from app.leads import LeadStore


def test_sanitize_clamps_garbage():
    a = sanitize({"intent": "launch_rockets", "products": [{"name": "x", "qty": -1}, "bad"], "budget": "lots"})
    assert a["intent"] == "other" and a["next_action"] == "call_back"
    assert a["products"] == [{"name": "x", "qty": None}] and a["budget"] is None


def test_hybrid_score_explains_itself():
    a = sanitize({"intent": "order", "products": [{"name": "x", "qty": 1}], "budget": 5, "urgency": "high"})
    score, reasons = hybrid_score(40, a)
    assert score == 95 and len(reasons) == 5
    spam, _ = hybrid_score(40, sanitize({"intent": "spam"}))
    assert spam == 0


def test_agent_creates_order_draft():
    lead, _ = LeadStore().add("Ivan", "whatsapp", phone="+998901112233",
                              message="Хочу заказать 2 шт кроссовки срочно")
    agent = CommerceAgent()
    res = agent.process(lead)
    assert res.order_draft and res.order_draft["items"][0]["qty"] == 2
    assert agent.metrics()["calls"] == 1
