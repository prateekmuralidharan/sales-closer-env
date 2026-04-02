# SalesCloserEnv

An OpenEnv environment that simulates realistic B2B sales conversations for training AI sales agents.

## Overview

SalesCloserEnv places an AI agent in a simulated sales call with an AI-powered prospect.
The agent must navigate multi-turn conversations to discover needs (BANT framework),
handle objections, and close deals — or correctly identify and disqualify unfit prospects.

## Tasks

| Task | Difficulty | Scenario | Goal |
|------|-----------|----------|------|
| warm_lead | Easy | Friendly inbound prospect (VP of Sales, TechScale Solutions) | Book a demo meeting |
| skeptic | Medium | Outbound cold call, competitor user, needs CTO buy-in | Get meeting with CTO |
| hostile_exec | Hard | Dismissive CEO with 5-minute patience (Nextera Systems) | Earn a follow-up call |
| tire_kicker | Expert | Enthusiastic but completely unqualified prospect (cafe chain) | Correctly disqualify |

## Action Space

| Field | Type | Values | Description |
|-------|------|--------|-------------|
| message | str | any | The salesperson's spoken message |
| action_type | str | "message", "close_attempt", "book_meeting", "disqualify" | Intent signal |

## Observation Space

| Field | Type | Description |
|-------|------|-------------|
| prospect_message | str | The prospect's latest reply |
| turn_number | int | Current turn (1-indexed) |
| max_turns | int | Maximum turns for this task (18) |
| task_id | str | Active task identifier |
| product_brief | dict | Product details (name, features, pricing, differentiators) |
| prospect_brief | dict | Visible prospect info (name, company, role, industry, size) |
| conversation_history | list | Full conversation so far |
| task_description | str | What the agent should accomplish |
| done | bool | Whether the episode has ended |
| termination_reason | str | Why the episode ended (if done) |

## Scoring

Scores range from 0.0 to 1.0, computed across 4 dimensions:

| Dimension | Weight | What It Measures |
|-----------|--------|-----------------|
| Discovery | 25% | BANT item uncovery (Budget, Authority, Need, Timeline) |
| Rapport | 15% | Personalization, name use, early questions, no monologues |
| Objection Handling | 25% | Acknowledging and addressing the prospect's objections |
| Outcome | 35% | Achieving the task's win condition |

## Setup

```bash
pip install fastapi uvicorn openai pydantic requests
```

## Running Locally

```bash
# Start the environment server
cd sales_closer_env
PYTHONPATH=. uvicorn server.app:app --host 0.0.0.0 --port 8000

# In a separate terminal, run the agent
export API_BASE_URL=<your-llm-endpoint>
export MODEL_NAME=<your-model>
export ENV_URL=http://localhost:8000
python inference.py
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| API_BASE_URL | Yes | OpenAI-compatible LLM API base URL |
| MODEL_NAME | Yes | Model identifier to use for all LLM calls |
| HF_TOKEN | No | API key / HuggingFace token (defaults to "x") |
| ENV_URL | No | Environment server URL for inference.py (default: http://localhost:8000) |

## Deployment

Built for Hugging Face Spaces with Docker. See `server/Dockerfile`.

The server exposes:
- `POST /reset` — start a new episode
- `POST /step` — take an action
- `GET /state` — get current episode metadata
- `GET /health` — health check
