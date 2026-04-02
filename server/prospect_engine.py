"""
Multi-layer prospect persona system.

Layer 1: Base personality (static, set at reset)
Layer 2: Scenario overlay (static, business context)
Layer 3: Emotional state guidance (dynamic, updated each turn)
"""
import os
from openai import OpenAI
from server.state_tracker import EmotionalState

client = OpenAI(
    base_url=os.environ.get("API_BASE_URL", ""),
    api_key=os.environ.get("HF_TOKEN", "x"),
)
MODEL = os.environ.get("MODEL_NAME", "")

PERSONALITY_PROMPTS = {
    "friendly": (
        "You are warm, approachable, and genuinely interested in the conversation. "
        "You answer questions openly and volunteer information. You use casual language."
    ),
    "guarded": (
        "You are professional but reserved. You give short answers and don't volunteer "
        "extra information. You need to be asked the right questions to open up."
    ),
    "blunt": (
        "You are direct, no-nonsense, and time-pressured. You interrupt if the salesperson "
        "rambles. You respect competence and despise generic pitches. You use short, clipped sentences."
    ),
    "enthusiastic": (
        "You are very excited and agreeable. You say 'that sounds great' to almost everything. "
        "You are chatty and ask lots of questions. You are genuinely friendly but not a serious buyer."
    ),
}


def build_scenario_prompt(profile: dict) -> str:
    hidden = profile["hidden"]
    visible = profile["visible"]
    objections_text = "\n".join(f"- {obj}" for obj in hidden.get("objections", []))
    dealbreakers_text = "\n".join(f"- {db}" for db in hidden.get("dealbreakers", []))

    return f"""You are {visible['name']}, {visible['role']} at {visible['company']} ({visible['industry']}, {visible['company_size']}).

YOUR SITUATION (you know this but only share if asked the right questions):
- Current solution: {hidden['current_solution']}
- Real pain point: {hidden['real_pain']}
- Secondary concern: {hidden.get('secondary_pain', 'None')}
- Budget: {hidden['budget']}
- Budget authority: {'You can approve this purchase' if hidden['has_budget_authority'] else 'You need approval from someone above you'}
- Timeline: {hidden['timeline']}
- Decision process: {hidden['decision_process']}

OBJECTIONS YOU WILL RAISE (bring these up naturally, one at a time, when the salesperson starts pitching):
{objections_text if objections_text else '- (none)'}

DEALBREAKERS (if the salesperson does any of these, get annoyed and consider ending the call):
{dealbreakers_text if dealbreakers_text else '- (none)'}

IMPORTANT RULES:
- Stay in character at all times
- Only share information when directly and relevantly asked
- Don't volunteer your budget or timeline unprompted
- React naturally to what the salesperson says
- If they ask good questions, warm up slightly
- If they monologue or are generic, get impatient
- Keep responses to 1-3 sentences (you're a busy professional)"""


def build_emotional_guidance(state: EmotionalState) -> str:
    trust_label = (
        "(warming up)" if state.trust > 0.6
        else "(still guarded)" if state.trust > 0.3
        else "(cold)"
    )
    patience_warning = " (getting impatient)" if state.patience < 0.4 else ""

    lines = [
        "YOUR CURRENT EMOTIONAL STATE (use this to guide your tone):",
        f"- Trust in this salesperson: {state.trust:.1f}/1.0 {trust_label}",
        f"- Patience remaining: {state.patience:.1f}/1.0{patience_warning}",
        f"- Engagement level: {state.engagement:.1f}/1.0",
    ]

    if state.prospect_ended_call:
        lines.append(
            "\nYOU ARE ABOUT TO END THIS CALL. Make your next response a polite but firm exit."
        )
    if state.dealbreaker_triggered:
        lines.append("\nThe salesperson triggered a dealbreaker. You are annoyed.")

    return "\n".join(lines)


def build_tire_kicker_addendum(task_config: dict) -> str:
    signals = (
        task_config.get("prospect_profile", {})
        .get("hidden", {})
        .get("tire_kicker_signals", [])
    )
    if not signals:
        return ""
    signals_text = "\n".join(f"- {s}" for s in signals)
    return f"\nSPECIAL BEHAVIOR (you are a tire kicker):\n{signals_text}"


def format_conversation(conversation_history: list) -> str:
    if not conversation_history:
        return "(conversation just started)"
    lines = []
    for msg in conversation_history:
        role = "Salesperson" if msg["role"] == "agent" else msg.get("name", "Prospect")
        lines.append(f"{role}: {msg['message']}")
    return "\n".join(lines)


def build_prospect_system_prompt(
    task_config: dict,
    emotional_state: EmotionalState,
    conversation_history: list,
) -> str:
    personality = PERSONALITY_PROMPTS[task_config["personality"]["communication_style"]]
    scenario = build_scenario_prompt(task_config["prospect_profile"])
    emotional_guidance = build_emotional_guidance(emotional_state)
    tire_kicker_addendum = build_tire_kicker_addendum(task_config)
    prospect_name = task_config["prospect_profile"]["visible"]["name"]

    # Cap conversation history to prevent token overflow: keep first 2 + last 6
    history = conversation_history
    if len(history) > 8:
        history = history[:2] + history[-6:]

    return f"""{personality}

{scenario}

{emotional_guidance}
{tire_kicker_addendum}

CONVERSATION SO FAR:
{format_conversation(history)}

Respond as {prospect_name}. Keep your response to 1-3 sentences. Stay in character."""


def generate_prospect_reply(
    task_config: dict,
    emotional_state: EmotionalState,
    conversation_history: list,
) -> str:
    """Call the LLM to generate the prospect's next message."""
    import time

    system_prompt = build_prospect_system_prompt(
        task_config, emotional_state, conversation_history
    )

    for attempt in range(5):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": system_prompt}],
                max_tokens=150,
                temperature=0.8,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            if "429" in str(e) and attempt < 4:
                wait = 10 * (attempt + 1)
                time.sleep(wait)
            else:
                raise
