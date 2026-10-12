from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_and_ui():
    assert client.get("/healthz").json() == {"status": "ok"}
    assert "LeadFlow AI" in client.get("/").text
    assert client.get("/version").json()["llm"]["backend"] == "mock"


def test_lead_flow_end_to_end():
    r = client.post("/leads", json={"name": "Ivan", "source": "whatsapp", "phone": "+998 90 999 00 11",
                                    "message": "Хочу заказать 2 шт кроссовки, срочно"})
    assert r.status_code == 201
    lead = r.json()["lead"]
    assert lead["agent"]["analysis"]["intent"] == "order"
    assert client.get(f"/leads/{lead['id']}").json()["agent"]["hybrid_score"] >= lead["score"]
    assert client.get("/orders").json()["count"] >= 1
    assert client.post(f"/leads/{lead['id']}/analyze").status_code == 200
    assert client.get("/metrics").json()["calls"] >= 2
    spam = client.post("/leads", json={"name": "S", "email": "s@spam.io", "message": "casino click here"})
    ids = [x["id"] for x in client.get("/leads", params={"min_score": 50}).json()["leads"]]
    assert lead["id"] in ids and spam.json()["lead"]["id"] not in ids


def test_validation():
    assert client.post("/leads", json={"name": "Nobody"}).status_code == 422
    assert client.get("/leads/99999").status_code == 404
