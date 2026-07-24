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

# In-memory ticket store (fine for a demo — resets when the server restarts)
tickets_by_phone: dict[str, list[dict]] = {}


class CheckinRequest(BaseModel):
    name: str
    phone: str
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

    tickets_by_phone.setdefault(req.phone, []).append(result)
    return result


@app.get("/api/tickets")
def get_tickets(phone: str):
    return tickets_by_phone.get(phone, [])


@app.get("/api/officers")
def list_officers():
    return officers_df.to_dict(orient="records")


@app.post("/api/reset")
def reset():
    reset_officers()
    tickets_by_phone.clear()
    return {"status": "reset"}

