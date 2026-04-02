"""
FastAPI application for SalesCloserEnv.

Exposes:
  POST /reset  — start a new episode
  POST /step   — take an action
  GET  /state  — get current episode state
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

from server.environment import SalesCloserEnvironment

app = FastAPI(title="SalesCloserEnv", version="1.0.0")

# Single shared environment instance (stateful, single-episode server)
env = SalesCloserEnvironment()


class ResetRequest(BaseModel):
    task_id: Optional[str] = "warm_lead"


class ActionPayload(BaseModel):
    message: str = ""
    action_type: str = "message"


class StepRequest(BaseModel):
    action: ActionPayload


@app.post("/reset")
def reset(request: ResetRequest = None):
    task_id = (request.task_id if request else None) or "warm_lead"
    result = env.reset(task_id=task_id)
    return result


@app.post("/step")
def step(request: StepRequest):
    if env.done:
        raise HTTPException(status_code=400, detail="Episode is done. Call /reset first.")
    action = {
        "message": request.action.message,
        "action_type": request.action.action_type,
    }
    result = env.step(action)
    return result


@app.get("/state")
def state():
    return env.get_state()


@app.get("/health")
def health():
    return {"status": "ok"}


def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
