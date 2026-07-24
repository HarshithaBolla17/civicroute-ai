# CivicRoute AI — web app

A working web version of the CivicRoute AI agent from the notebook: FastAPI backend
running the LangGraph + Gemini agent, plus a static HTML/JS frontend kiosk.

## Structure
```
backend/    FastAPI app + agent.py (the LangGraph graph)
frontend/   Static HTML/CSS/JS kiosk page
```

## Deploy order
1. Push this whole folder to a new GitHub repo.
2. Deploy `backend/` to Render (Web Service, root directory `backend`,
   build command `pip install -r requirements.txt`, start command
   `uvicorn main:app --host 0.0.0.0 --port $PORT`, env var `GOOGLE_API_KEY`).
3. Copy the Render URL into `frontend/config.js` (`API_BASE_URL`).
4. Deploy `frontend/` to Vercel (root directory `frontend`, no build step needed).

See the step-by-step walkthrough in chat for exact clicks.
