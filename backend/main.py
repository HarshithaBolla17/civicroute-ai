from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent import graph, officers_df, reset_officers

app = FastAPI(title="CivicRoute AI")

# Allow the frontend (hosted on a different domain, e.g. Vercel) to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CheckinRequest(BaseModel):
    name: str
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
            "zone": req.zone,
            "issue": req.issue,
            "department": "",
            "urgency": "",
            "reasoning": "",
            "assigned_officer": "",
        }
    )
    return result


@app.get("/api/officers")
def list_officers():
    return officers_df.to_dict(orient="records")


@app.post("/api/reset")
def reset():
    reset_officers()
    return {"status": "reset"}
