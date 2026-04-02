"""
SalesCloserEnv client — thin HTTP wrapper around the environment server.
"""
import os
import requests


class SalesCloserClient:
    """HTTP client for interacting with the SalesCloserEnv server."""

    def __init__(self, base_url: str = None):
        self.base_url = (base_url or os.environ.get("ENV_URL", "http://localhost:8000")).rstrip("/")

    def reset(self, task_id: str = "warm_lead") -> dict:
        resp = requests.post(f"{self.base_url}/reset", json={"task_id": task_id}, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def step(self, message: str, action_type: str = "message") -> dict:
        payload = {"action": {"message": message, "action_type": action_type}}
        resp = requests.post(f"{self.base_url}/step", json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json()

    def get_state(self) -> dict:
        resp = requests.get(f"{self.base_url}/state", timeout=10)
        resp.raise_for_status()
        return resp.json()
