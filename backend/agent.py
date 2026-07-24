import os
from typing import TypedDict, Literal

import pandas as pd
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage


# ---------- Shared state ----------
class ReportState(TypedDict):
    name: str
    phone: str
    zone: str
    issue: str
    department: str
    urgency: str
    reasoning: str
    assigned_officer: str


# ---------- Officer data (swap for a real database later) ----------
officers_df = pd.DataFrame(
    [
        {"officer_name": "R. Naidu", "department": "roads", "status": "active", "next_slot": "10:00 AM"},
        {"officer_name": "S. Patil", "department": "roads", "status": "active", "next_slot": "10:20 AM"},
        {"officer_name": "A. George", "department": "sanitation", "status": "active", "next_slot": "9:40 AM"},
        {"officer_name": "M. Fernandes", "department": "sanitation", "status": "active", "next_slot": "10:10 AM"},
        {"officer_name": "K. Reddy", "department": "electrical", "status": "active", "next_slot": "9:30 AM"},
        {"officer_name": "V. Shah", "department": "electrical", "status": "active", "next_slot": "9:55 AM"},
        {"officer_name": "T. Bose", "department": "water", "status": "active", "next_slot": "10:05 AM"},
        {"officer_name": "J. Kurian", "department": "water", "status": "active", "next_slot": "10:25 AM"},
    ]
)


def reset_officers():
    """Set every officer back to active — used by the /api/reset endpoint."""
    officers_df["status"] = "active"


# ---------- Gemini client (created lazily so a missing key doesn't crash startup) ----------
_llm = None


def get_llm():
    global _llm
    if _llm is None:
        _llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", temperature=0)
    return _llm


ROUTER_SYSTEM_PROMPT = """You are a civic-issue router for a city municipal corporation.
Based on the citizen's description, classify the issue into exactly ONE of these words:
roads, sanitation, electrical, water.

roads: potholes, broken footpaths, damaged speed breakers, faulty traffic signals
sanitation: garbage overflow, blocked drains, sewage leaks, waste collection
electrical: streetlight failure, exposed wiring, transformer issues, power outages
water: pipe leaks, no water supply, contaminated water, broken taps

Respond with only one word: roads, sanitation, electrical, or water."""

HAZARD_KEYWORDS = [
    "exposed wire", "live wire", "gas leak", "open manhole",
    "building collapse", "electrocution", "fire", "short circuit",
]


# ---------- Nodes ----------
def intake_node(state: ReportState):
    # The API layer already fills name/zone/issue before invoking the graph,
    # so this node is just a pass-through — it exists to keep the same
    # intake -> router -> department -> officer_check shape as the notebook.
    return state


def router_node(state: ReportState):
    issue_lower = state["issue"].lower()

    # Hard safety net: hazards are flagged no matter what the model says
    if any(keyword in issue_lower for keyword in HAZARD_KEYWORDS):
        return {
            "department": "electrical",
            "urgency": "hazard",
            "reasoning": "matched a hard-coded hazard keyword \u2014 escalated by the safety net",
        }

    response = get_llm().invoke(
        [
            SystemMessage(content=ROUTER_SYSTEM_PROMPT),
            HumanMessage(content=state["issue"]),
        ]
    )

    # Newer Gemini responses can come back as a string OR a list of content parts
    content = response.content
    if isinstance(content, list):
        raw = "".join(
            part if isinstance(part, str) else part.get("text", "")
            for part in content
        ).strip().lower()
    else:
        raw = content.strip().lower()

    if "roads" in raw:
        dept = "roads"
    elif "sanitation" in raw:
        dept = "sanitation"
    elif "electrical" in raw:
        dept = "electrical"
    elif "water" in raw:
        dept = "water"
    else:
        dept = "roads"  # safe fallback

    return {
        "department": dept,
        "urgency": "routine",
        "reasoning": f"Gemini classified based on: {state['issue']}",
    }


def roads_node(state: ReportState):
    return state


def sanitation_node(state: ReportState):
    return state


def electrical_node(state: ReportState):
    return state


def water_node(state: ReportState):
    return state


def officer_availability_node(state: ReportState):
    dept = state["department"]
    available = officers_df[(officers_df["department"] == dept) & (officers_df["status"] == "active")]

    if not available.empty:
        officer_name = available.iloc[0]["officer_name"]
        officers_df.loc[available.index[0], "status"] = "busy"
        return {"assigned_officer": officer_name}
    else:
        return {"assigned_officer": "none - queued"}


def route_decision(state: ReportState) -> Literal["roads", "sanitation", "electrical", "water"]:
    return state["department"]


def build_graph():
    builder = StateGraph(ReportState)

    builder.add_node("intake", intake_node)
    builder.add_node("router", router_node)
    builder.add_node("roads", roads_node)
    builder.add_node("sanitation", sanitation_node)
    builder.add_node("electrical", electrical_node)
    builder.add_node("water", water_node)
    builder.add_node("officer_check", officer_availability_node)

    builder.set_entry_point("intake")
    builder.add_edge("intake", "router")

    builder.add_conditional_edges(
        "router",
        route_decision,
        {
            "roads": "roads",
            "sanitation": "sanitation",
            "electrical": "electrical",
            "water": "water",
        },
    )

    builder.add_edge("roads", "officer_check")
    builder.add_edge("sanitation", "officer_check")
    builder.add_edge("electrical", "officer_check")
    builder.add_edge("water", "officer_check")
    builder.add_edge("officer_check", END)

    return builder.compile()


graph = build_graph()
