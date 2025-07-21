# report_contract.py  ─────────────────────────────────────────────────────────
"""
A Pydantic model that both the producers (Gradio apps) and the consumer
(report_agent) agree on.  Add / rename fields whenever you like – all apps
see the same truth here.
"""
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid, datetime as dt

class IOC(BaseModel):
    type: str
    value: str
    source: Optional[str] = ""

class MiniReport(BaseModel):
    # ── required ────────────────────────────────────────────────────────────
    title: str = Field(default="Untitled Sub-Report")
    executive_summary: str
    findings: str                                           # free-text
    iocs: List[IOC] = []
    recommendations: str

    # ── optional but nice to have ───────────────────────────────────────────
    incident_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category: str = "—"
    timeline: str = "—"
    produced_at: dt.date = Field(default_factory=dt.date.today)