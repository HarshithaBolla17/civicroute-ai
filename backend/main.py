from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
from datetime import datetime, timezone

from agent import graph, officers_df, reset_officers

app = FastAPI(title="CivicRoute AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CheckinRequest(BaseModel):
    name: str
    phone: str          # <-- was missing, so it was silently dropped
    zone: str
    issue: str


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/checkin")
def checkin(req: CheckinRequest):
    result = graph.invoke(
        {
            "name": req.name,
            "phone": req.phone,
            "zone": req.zone,
            "issue": req.issue,
            "department": "",
            "urgency": "",
            "reasoning": "",
            "assigned_officer": "",
        }
    )
    result["ticket_id"] = f"CR-{uuid.uuid4().hex[:6].upper()}"
    result["filed_at"] = datetime.now(timezone.utc).strftime("%b %d, %I:%M %p UTC")
    return result

@app.post("/api/reset")
def reset():
    reset_officers()
    return {"status": "reset"}
