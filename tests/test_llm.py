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


# ---------------------------------------------------------------- AMD Token Factory one-key path
from app.llm import DEFAULT_TOKEN_FACTORY_MODEL, TOKEN_FACTORY_BASE_URL, _settings, check  # noqa: E402

_LLM_VARS = ("LLM_BACKEND", "LLM_BASE_URL", "LLM_MODEL", "LLM_API_KEY", "LLM_HARDWARE", "LLM_JSON_MODE",
             "AMD_TOKEN_FACTORY_API_KEY", "RADEON_API_KEY", "AMD_TOKEN_FACTORY_MODEL",
             "AMD_TOKEN_FACTORY_BASE_URL", "TOKEN_FACTORY_BASE_URL")


@pytest.fixture
def clean_env(monkeypatch):
    for k in _LLM_VARS:
        monkeypatch.delenv(k, raising=False)
    return monkeypatch


def test_no_key_defaults_to_mock(clean_env):
    cfg = _settings()
    assert cfg["backend"] == "mock" and cfg["provider"] == "mock"
    assert LLMClient().analyze("price?").backend == "mock"


@pytest.mark.parametrize("var", ["AMD_TOKEN_FACTORY_API_KEY", "RADEON_API_KEY"])
def test_token_factory_key_selects_openai(clean_env, var):
    clean_env.setenv(var, "rc-test")
    cfg = _settings()
    assert cfg["backend"] == "openai" and cfg["provider"] == "amd-token-factory"
    assert cfg["base_url"] == TOKEN_FACTORY_BASE_URL == "https://developer.amd.com.cn/radeon/api/v1"
    assert cfg["model"] == DEFAULT_TOKEN_FACTORY_MODEL == "DeepSeek-V4-Flash"
    assert cfg["api_key"] == "rc-test" and "Token Factory" in cfg["hardware"]


def test_token_factory_request_goes_to_amd(clean_env):
    clean_env.setenv("AMD_TOKEN_FACTORY_API_KEY", "rc-abc")
    clean_env.setenv("AMD_TOKEN_FACTORY_MODEL", "Qwen3.8-27B")
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["auth"] = request.headers["authorization"]
        return _fake_vllm(request)

    res = LLMClient(transport=httpx.MockTransport(handler)).analyze("3 tea please")
    assert seen["url"] == "https://developer.amd.com.cn/radeon/api/v1/chat/completions"
    assert seen["auth"] == "Bearer rc-abc"
    assert res.backend == "openai" and res.model == "Qwen3.8-27B"
    assert res.extra["provider"] == "amd-token-factory"


def test_explicit_mock_and_llm_overrides_win(clean_env):
    clean_env.setenv("RADEON_API_KEY", "rc-test")
    clean_env.setenv("LLM_BACKEND", "mock")
    assert _settings()["backend"] == "mock"
    assert LLMClient().analyze("price?").backend == "mock"
    clean_env.setenv("LLM_BACKEND", "openai")
    clean_env.setenv("LLM_BASE_URL", "http://mi300x:8000/v1/")
    clean_env.setenv("LLM_MODEL", "Qwen/Qwen2.5-7B-Instruct")
    clean_env.setenv("AMD_TOKEN_FACTORY_MODEL", "ignored")
    cfg = _settings()
    assert cfg["base_url"] == "http://mi300x:8000/v1" and cfg["model"] == "Qwen/Qwen2.5-7B-Instruct"
    assert cfg["provider"] == "openai-compatible"


def test_blank_env_values_count_as_unset(clean_env):
    clean_env.setenv("LLM_BACKEND", "")
    clean_env.setenv("LLM_BASE_URL", "")
    clean_env.setenv("AMD_TOKEN_FACTORY_API_KEY", "rc-test")
    cfg = _settings()
    assert cfg["backend"] == "openai" and cfg["base_url"] == TOKEN_FACTORY_BASE_URL


def test_json_mode_toggle(clean_env):
    clean_env.setenv("AMD_TOKEN_FACTORY_API_KEY", "rc-test")
    clean_env.setenv("LLM_JSON_MODE", "0")
    bodies = []

    def handler(request):
        bodies.append(json.loads(request.content))
        return _fake_vllm(request)

    LLMClient(transport=httpx.MockTransport(handler)).analyze("3 tea please")
    assert "response_format" not in bodies[0]


def test_check_lists_models_and_runs_sample(clean_env):
    clean_env.setenv("RADEON_API_KEY", "rc-test")

    def handler(request):
        if request.url.path.endswith("/models"):
            return httpx.Response(200, json={"data": [{"id": "DeepSeek-V4-Flash"}, {"id": "GLM-5.3-Flash"}]})
        return _fake_vllm(request)

    out = check(transport=httpx.MockTransport(handler))
    assert out["ok"] and out["model_available"] and out["provider"] == "amd-token-factory"
    assert "rc-test" not in json.dumps(out)
    clean_env.delenv("RADEON_API_KEY")
    assert check()["ok"] is False


def test_env_example_plus_one_key_goes_live(clean_env, tmp_path):
    """`cp .env.example .env` + only the key filled in => Token Factory live config."""
    import os
    from pathlib import Path
    from unittest import mock

    import serve

    example = (Path(__file__).parent.parent / ".env.example").read_text(encoding="utf-8")
    env = tmp_path / ".env"
    env.write_text(example.replace("AMD_TOKEN_FACTORY_API_KEY=\n", "AMD_TOKEN_FACTORY_API_KEY=rc-from-file\n"))
    for k in ("LLM_TIMEOUT", "LLM_FALLBACK"):
        clean_env.delenv(k, raising=False)
    with mock.patch.dict(os.environ):  # loader writes os.environ directly; restore afterwards
        serve.load_dotenv(env)
        cfg = _settings()
    assert cfg["backend"] == "openai" and cfg["provider"] == "amd-token-factory"
    assert cfg["base_url"] == TOKEN_FACTORY_BASE_URL and cfg["api_key"] == "rc-from-file"
    assert cfg["model"] == "DeepSeek-V4-Flash"
    assert "AMD_TOKEN_FACTORY_API_KEY" not in os.environ


def test_mock_uz_complaint_detected_as_uzbek():
    d = mock_analyze("Kurtka brak keldi, pulni qaytaring")
    assert d["language"] == "uz" and d["intent"] == "complaint" and d["next_action"] == "escalate"
