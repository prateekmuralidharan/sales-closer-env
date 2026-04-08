"""
inference.py — Baseline Sales Agent for SalesCloserEnv

STDOUT FORMAT (required):
    [START] task=<task_name> env=<benchmark> model=<model_name>
    [STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
    [END]   success=<true|false> steps=<n> score=<score> rewards=<r1,r2,...,rn>

Required env vars:
  API_BASE_URL  — LLM API endpoint
  MODEL_NAME    — model identifier
  HF_TOKEN      — Hugging Face / API key
  ENV_URL       — environment server URL (default: http://localhost:8000)
"""

import os
import sys
import time
from typing import List, Optional

try:
    import requests
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "requests"])
    import requests

try:
    from openai import OpenAI
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "openai"])
    from openai import OpenAI

API_BASE_URL = os.getenv("API_BASE_URL") or "https://api.groq.com/openai/v1"
MODEL_NAME = os.getenv("MODEL_NAME") or "llama-3.1-8b-instant"
API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
ENV_URL = os.getenv("ENV_URL", "http://localhost:8000").rstrip("/")
BENCHMARK = "sales-closer-env"

client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

TASKS = ["warm_lead", "skeptic", "hostile_exec", "tire_kicker"]


# ── Structured logging ────────────────────────────────────────────────────────

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    action_safe = action.replace("\n", " ")[:80]
    print(f"[STEP] step={step} action={action_safe} reward={reward:.2f} done={done_val} error={error_val}", flush=True)


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)


# ── Agent logic ───────────────────────────────────────────────────────────────

AGENT_SYSTEM_PROMPT = """You are an expert B2B sales development representative (SDR). You are on a live sales call with a prospect.

YOUR METHODOLOGY (SPIN Selling):
Follow this sequence naturally through the conversation:

1. SITUATION QUESTIONS (turns 1-4): Understand their current state
   - "What tools are you currently using for [domain]?"
   - "How is your team structured?"
   - "Walk me through your current process for [task]?"

2. PROBLEM QUESTIONS (turns 4-8): Uncover pain points
   - "What's the biggest challenge you face with [current approach]?"
   - "Where do you feel the most friction?"
   - "How does [problem] affect your team's performance?"

3. IMPLICATION QUESTIONS (turns 8-12): Deepen the pain
   - "What happens if this issue isn't resolved in the next quarter?"
   - "How much time/money does your team lose to [problem] each month?"
   - "How does this affect [related business outcome]?"

4. NEED-PAYOFF QUESTIONS (turns 12-15): Let them articulate the value
   - "If you could [solve problem], what would that mean for [metric]?"
   - "How would your team's day change if [solution]?"

5. CLOSE (turns 15-18): Propose a next step
   - "Based on what you've shared, I think [product] could help with [specific pain]. Would it make sense to schedule a deeper demo with [relevant stakeholder] next week?"

CRITICAL RULES:
- LISTEN more than you talk. Keep responses under 100 words.
- ALWAYS ask at least one question per response.
- NEVER pitch features before turn 8 unless directly asked.
- Use the prospect's NAME at least twice in the conversation.
- Reference their COMPANY and INDUSTRY specifically.
- When they raise an objection: ACKNOWLEDGE it first ("I hear you..."), then address it.
- If you suspect the prospect is not qualified (no budget, no authority, no real need), ask direct qualifying questions and be ready to DISQUALIFY politely.

DISQUALIFICATION PROTOCOL:
If after asking budget, authority, need, and timeline questions, the prospect clearly lacks 2+ of these, you MUST disqualify. Say something like:
"I really appreciate your time, [name]. Based on what you've shared, it sounds like [product] might not be the best fit for [company] right now, especially given [reason]. I'd love to reconnect when [condition changes]. In the meantime, I'll send over some resources that might help with [their minor pain]."
Signs the prospect is NOT qualified (disqualify if you see 2+):
- No budget or budget owner is someone else entirely
- No real pain — problems are "minor annoyances" not business-critical
- No timeline — "maybe someday" or "not planning to scale"
- No authority — can't make or influence the decision
Then set your action_type to "disqualify".

CLOSING PROTOCOL:
When you've completed discovery and the prospect seems ready, don't be vague. Propose a specific next step:
"[Name], I think there's a strong fit here. Would you be open to a 30-minute demo next [day] where I can show you exactly how [product] handles [their specific pain]?"
Then set your action_type to "book_meeting".

OUTPUT FORMAT:
Respond with ONLY your spoken message. No meta-commentary, no stage directions, no parentheticals. Just what you would actually say on the call."""


def decide_action_type(
    agent_message: str,
    turn_number: int,
    max_turns: int,
    conversation: list = None,
) -> str:
    msg_lower = agent_message.lower()

    disqualify_signals = [
        "not the best fit", "might not be right", "reconnect when", "not a match",
        "better suited for", "not the right time", "not the right fit",
        "not the right solution", "doesn't seem like", "doesn't sound like",
        "may not be the right", "might not be the right", "probably not the right",
        "best of luck", "wish you the best",
        "not a good fit", "not a great fit", "send over some resources",
        "reach out when", "circle back when", "touch base when",
    ]
    if turn_number >= 6 and any(signal in msg_lower for signal in disqualify_signals):
        return "disqualify"

    if turn_number >= 8 and conversation:
        prospect_text = " ".join(
            m["message"].lower() for m in conversation if m["role"] == "prospect"
        )
        unqualified_signals = [
            "just exploring", "no rush", "not planning", "owner would need",
            "minor annoyance", "minor frustration", "not too bad", "managed fine",
            "no budget", "don't have budget", "can't approve", "need approval",
            "not a priority", "maybe someday", "not sure we need",
        ]
        hits = sum(1 for s in unqualified_signals if s in prospect_text)
        if hits >= 3:
            return "disqualify"

    close_signals = [
        "schedule a demo", "book a meeting", "set up a call", "next step",
        "30-minute demo", "follow-up meeting", "would you be open to",
        "set up time", "get something on the calendar",
    ]
    if any(signal in msg_lower for signal in close_signals) and turn_number >= 10:
        return "book_meeting"

    if turn_number >= max_turns - 2:
        return "close_attempt"

    return "message"


def build_user_prompt(observation: dict, conversation: list) -> str:
    product = observation.get("product_brief", {})
    prospect = observation.get("prospect_brief", {})
    task_desc = observation.get("task_description", "")

    prompt = f"""TASK: {task_desc}

PRODUCT YOU'RE SELLING:
- Name: {product.get('name', '')}
- Category: {product.get('category', '')}
- Key Features: {', '.join(product.get('key_features', []))}
- Pricing: {product.get('pricing', '')}
- Ideal Customer: {product.get('ideal_customer', '')}
- Differentiators: {', '.join(product.get('differentiators', []))}

PROSPECT INFO:
- Name: {prospect.get('name', '')}
- Role: {prospect.get('role', '')}
- Company: {prospect.get('company', '')}
- Industry: {prospect.get('industry', '')}
- Company Size: {prospect.get('company_size', '')}

CONVERSATION SO FAR:
"""
    prospect_name = prospect.get("name", "Prospect")
    for msg in conversation:
        role_label = "You" if msg["role"] == "agent" else prospect_name
        prompt += f"{role_label}: {msg['message']}\n"

    prospect_last = observation.get("prospect_message", "")
    if prospect_last:
        prompt += f"{prospect_name}: {prospect_last}\n"

    turn = observation.get("turn_number", 0)
    max_turns = observation.get("max_turns", 18)
    prompt += f"\nTurn {turn}/{max_turns}. Respond as the salesperson."

    return prompt


def run_task(task_id: str) -> None:
    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False

    log_start(task=task_id, env=BENCHMARK, model=MODEL_NAME)

    try:
        reset_resp = requests.post(
            f"{ENV_URL}/reset",
            json={"task_id": task_id},
            timeout=30,
        )
        reset_resp.raise_for_status()
        data = reset_resp.json()
        observation = data["observation"]

        conversation: list = []
        done = False

        while not done:
            user_prompt = build_user_prompt(observation, conversation)

            agent_message = ""
            step_error = None
            for attempt in range(5):
                try:
                    response = client.chat.completions.create(
                        model=MODEL_NAME,
                        messages=[
                            {"role": "system", "content": AGENT_SYSTEM_PROMPT},
                            {"role": "user", "content": user_prompt},
                        ],
                        max_tokens=200,
                        temperature=0.7,
                    )
                    agent_message = response.choices[0].message.content.strip()
                    break
                except Exception as e:
                    if "429" in str(e) and attempt < 4:
                        time.sleep(10 * (attempt + 1))
                    else:
                        step_error = str(e)
                        agent_message = "I appreciate your time. Let me follow up with more details."
                        break

            action_type = decide_action_type(
                agent_message,
                observation.get("turn_number", 0),
                observation.get("max_turns", 18),
                conversation,
            )

            step_resp = requests.post(
                f"{ENV_URL}/step",
                json={"action": {"message": agent_message, "action_type": action_type}},
                timeout=60,
            )
            step_resp.raise_for_status()
            step_data = step_resp.json()

            observation = step_data["observation"]
            reward = step_data["reward"]
            done = step_data["done"]
            steps_taken += 1

            rewards.append(reward)
            log_step(
                step=steps_taken,
                action=f"{action_type}:{agent_message[:60]}",
                reward=reward,
                done=done,
                error=step_error,
            )

            conversation.append({"role": "agent", "message": agent_message})
            if not done and observation.get("prospect_message"):
                conversation.append({"role": "prospect", "message": observation["prospect_message"]})

            if done:
                score = reward
                success = score >= 0.5

            time.sleep(2)

    except Exception as e:
        score = 0.0
        success = False
        print(f"[DEBUG] Task {task_id} error: {e}", flush=True)

    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)


if __name__ == "__main__":
    for task_id in TASKS:
        run_task(task_id)
