import json

import httpx
import pytest

from app.llm import LLMClient, extract_json, mock_analyze


def test_mock_ru_order():
    d = mock_analyze("Хочу заказать 2 шт кроссовки, срочно, бюджет 900000 сум")
    assert d["intent"] == "order" and d["language"] == "ru" and d["urgency"] == "high"
    assert d["products"][0] == {"name": "кроссовки", "qty": 2}
    assert d["budget"] == 900000 and d["currency"] == "UZS"


def test_mock_uz_and_en_and_spam():
    assert mock_analyze("Salom, narxi qancha?")["language"] == "uz"
    assert mock_analyze("What is the price for 50 units hoodies?")["intent"] == "quote"
    assert mock_analyze("crypto bonus casino")["next_action"] == "ignore"


def test_extract_json_tolerates_fences():
    assert extract_json('```json\n{"a": 1}\n```') == {"a": 1}
    with pytest.raises(ValueError):
        extract_json("nope")


def _fake_vllm(request: httpx.Request) -> httpx.Response:
    body = json.loads(request.content)
    assert request.url.path.endswith("/chat/completions")
    assert body["messages"][0]["role"] == "system"
    content = json.dumps({"intent": "order", "language": "en", "products": [{"name": "tea", "qty": 3}],
                          "budget": 20, "currency": "USD", "urgency": "normal", "reply": "Sure!",
                          "next_action": "create_order_draft", "rationale": "explicit order"})
    return httpx.Response(200, json={"model": body["model"], "choices": [{"message": {"content": content}}],
                                     "usage": {"prompt_tokens": 100, "completion_tokens": 50}})


def test_openai_compatible_backend(monkeypatch):
    monkeypatch.setenv("LLM_BACKEND", "openai")
    res = LLMClient(transport=httpx.MockTransport(_fake_vllm)).analyze("3 tea please")
    assert res.backend == "openai" and res.data["products"][0]["name"] == "tea"
    assert res.completion_tokens == 50 and res.tokens_per_sec > 0


def test_fallback_when_gpu_endpoint_down(monkeypatch):
    monkeypatch.setenv("LLM_BACKEND", "openai")
    down = httpx.MockTransport(lambda r: httpx.Response(503))
    res = LLMClient(transport=down).analyze("price?")
    assert res.backend == "mock" and res.fallback_reason
    monkeypatch.setenv("LLM_FALLBACK", "0")
    with pytest.raises(httpx.HTTPStatusError):
        LLMClient(transport=down).analyze("price?")
