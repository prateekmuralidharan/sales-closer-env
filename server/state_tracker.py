"""
Emotional state tracker for the prospect.

All updates are deterministic (no LLM calls) to ensure reproducibility.
"""
from dataclasses import dataclass, field


@dataclass
class EmotionalState:
    trust: float = 0.3          # 0-1, starts low
    patience: float = 0.7       # 0-1, decreases with bad behavior
    engagement: float = 0.5     # 0-1, increases with good questions
    objections_raised: list = field(default_factory=list)
    objections_handled: list = field(default_factory=list)
    discovered_by_agent: list = field(default_factory=list)  # BANT items uncovered
    dealbreaker_triggered: bool = False
    prospect_ended_call: bool = False


def update_state(
    state: EmotionalState,
    agent_message: str,
    task_config: dict,
    turn_number: int,
) -> EmotionalState:
    """Apply deterministic rules to update emotional state after each agent message."""
    if not agent_message:
        return state

    msg_lower = agent_message.lower()
    prospect_name = task_config["prospect_profile"]["visible"]["name"].split()[0].lower()

    # --- TRUST ---
    # +0.05 if agent used prospect's name
    if prospect_name in msg_lower:
        state.trust = min(1.0, state.trust + 0.05)

    # +0.05 if agent asked a question
    if "?" in agent_message:
        state.trust = min(1.0, state.trust + 0.05)

    # +0.08 if agent referenced prospect's company or industry
    company = task_config["prospect_profile"]["visible"]["company"].lower()
    industry = task_config["prospect_profile"]["visible"]["industry"].lower()
    if company in msg_lower or any(word in msg_lower for word in industry.split() if len(word) > 3):
        state.trust = min(1.0, state.trust + 0.08)

    # -0.1 if agent message is too long (monologue — over 150 words)
    word_count = len(agent_message.split())
    if word_count > 150:
        state.trust = max(0.0, state.trust - 0.1)

    # --- PATIENCE ---
    # Natural decay per turn (faster for impatient personalities)
    patience_decay = 0.08 if task_config["personality"]["patience_level"] < 0.5 else 0.04
    state.patience = max(0.0, state.patience - patience_decay)

    # -0.15 if agent monologues (>150 words without a question)
    if word_count > 150 and "?" not in agent_message:
        state.patience = max(0.0, state.patience - 0.15)

    # +0.05 if message is concise and has a question (<80 words with ?)
    if word_count < 80 and "?" in agent_message:
        state.patience = min(1.0, state.patience + 0.05)

    # --- ENGAGEMENT ---
    # +0.1 if agent asks about pain/challenges/problems
    pain_keywords = [
        "challenge", "problem", "struggle", "pain", "frustrate",
        "difficult", "issue", "concern", "worry",
    ]
    if any(kw in msg_lower for kw in pain_keywords):
        state.engagement = min(1.0, state.engagement + 0.1)

    # -0.1 if agent is just pitching without asking
    pitch_keywords = [
        "feature", "our platform", "our solution", "we offer",
        "we provide", "our product",
    ]
    if any(kw in msg_lower for kw in pitch_keywords) and "?" not in agent_message:
        state.engagement = max(0.0, state.engagement - 0.1)

    # --- DEALBREAKER CHECK ---
    for db in task_config["prospect_profile"]["hidden"].get("dealbreakers", []):
        db_keywords = [w for w in db.lower().split() if len(w) > 2]
        if not db_keywords:
            continue
        matches = sum(1 for kw in db_keywords if kw in msg_lower)
        if matches >= max(1, len(db_keywords) // 2):
            state.dealbreaker_triggered = True

    # --- END CALL CHECK ---
    if state.patience <= 0.1 or state.dealbreaker_triggered:
        state.prospect_ended_call = True

    return state
