"""HTTP layer for LeadFlow AI (commerce lead & order agent on AMD)."""

from __future__ import annotations

import os
from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.agent import CommerceAgent
from app.leads import LeadStore

ROOT = Path(__file__).resolve().parent
_VERSION_FILE = ROOT.parent / "VERSION"
VERSION = os.getenv("APP_VERSION") or (
    _VERSION_FILE.read_text().strip() if _VERSION_FILE.exists() else "dev"
)

app = FastAPI(title="LeadFlow AI", version=VERSION)
store = LeadStore()
agent = CommerceAgent()


class LeadIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    source: str = Field(default="web", max_length=40)
    email: str | None = Field(default=None, max_length=320)
    phone: str | None = Field(default=None, max_length=40)
    message: str | None = Field(default=None, max_length=5000)
    analyze: bool = True


def _view(lead) -> dict:
    out = asdict(lead)
    a = agent.analyses.get(lead.id)
    out["agent"] = asdict(a) if a else None
    return out


@app.get("/", include_in_schema=False)
def ui() -> FileResponse:
    return FileResponse(ROOT / "static" / "index.html")


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


@app.get("/version")
def version() -> dict:
    return {"version": VERSION, "commit": os.getenv("GIT_COMMIT", "unknown"), "llm": agent.llm.info}


@app.post("/leads", status_code=201)
def create_lead(payload: LeadIn) -> dict:
    data = payload.model_dump()
    analyze = data.pop("analyze")
    try:
        lead, created = store.add(**data)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if analyze and (created or lead.id not in agent.analyses) and lead.message:
        agent.process(lead)
    return {"created": created, "lead": _view(lead)}


@app.post("/leads/{lead_id}/analyze")
def analyze_lead(lead_id: int) -> dict:
    lead = store.get(lead_id)
    if lead is None:
        raise HTTPException(status_code=404, detail="lead not found")
    return asdict(agent.process(lead))


@app.get("/leads")
def list_leads(min_score: int = Query(default=0, ge=0, le=100)) -> dict:
    leads = [_view(lead) for lead in store.list()]
    leads = [v for v in leads if (v["agent"]["hybrid_score"] if v["agent"] else v["score"]) >= min_score]
    leads.sort(key=lambda v: -(v["agent"]["hybrid_score"] if v["agent"] else v["score"]))
    return {"count": len(leads), "leads": leads}


@app.get("/leads/{lead_id}")
def get_lead(lead_id: int) -> dict:
    lead = store.get(lead_id)
    if lead is None:
        raise HTTPException(status_code=404, detail="lead not found")
    return _view(lead)


@app.get("/orders")
def list_orders() -> dict:
    return {"count": len(agent.orders), "orders": [asdict(o) for o in agent.orders.values()]}


@app.get("/metrics")
def metrics() -> dict:
    return agent.metrics()
