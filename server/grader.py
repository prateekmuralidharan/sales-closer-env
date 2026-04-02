"""
Reward computation & scoring for SalesCloserEnv.

Four dimensions:
  - Discovery (25%): BANT item uncovery
  - Rapport (15%): Personalization and conversational quality
  - Objection Handling (25%): Acknowledgment and resolution of objections
  - Outcome (35%): Achieving the task's win condition
"""
from server.state_tracker import EmotionalState

BANT_ITEMS = ["budget", "authority", "need", "timeline"]


def score_discovery(conversation_history: list, task_config: dict) -> float:
    """Score how many BANT items the agent successfully uncovered."""
    hidden = task_config["prospect_profile"]["hidden"]

    budget_ask_kws = ["budget", "spend", "invest", "cost", "afford", "price range", "allocated"]
    budget_reveal_kws = hidden["budget"].lower().split() + ["month", "annual", "year"]

    authority_ask_kws = ["decision", "approve", "sign off", "authority", "who else", "stakeholder", "involved"]
    authority_reveal_kws = ["approve", "boss", "cto", "ceo", "board", "procurement", "i can decide", "need approval"]

    need_ask_kws = ["challenge", "problem", "pain", "struggle", "looking for", "need", "goal", "trying to"]
    need_reveal_kws = hidden["real_pain"].lower().split()[:5]

    timeline_ask_kws = ["timeline", "when", "deadline", "urgency", "implement", "go live", "start"]
    timeline_reveal_kws = hidden["timeline"].lower().split()[:5]

    bant_checks = [
        (budget_ask_kws, budget_reveal_kws),
        (authority_ask_kws, authority_reveal_kws),
        (need_ask_kws, need_reveal_kws),
        (timeline_ask_kws, timeline_reveal_kws),
    ]

    agent_messages = [m["message"] for m in conversation_history if m["role"] == "agent"]
    prospect_messages = [m["message"] for m in conversation_history if m["role"] == "prospect"]

    all_agent_text = " ".join(agent_messages).lower()
    all_prospect_text = " ".join(prospect_messages).lower()

    discovered = 0.0
    for ask_kws, reveal_kws in bant_checks:
        agent_asked = any(kw in all_agent_text for kw in ask_kws)
        prospect_revealed = any(kw in all_prospect_text for kw in reveal_kws)
        if agent_asked and prospect_revealed:
            discovered += 1
        elif agent_asked:
            discovered += 0.5  # Partial credit for asking even if prospect didn't reveal

    return discovered / len(BANT_ITEMS)


def score_rapport(conversation_history: list, task_config: dict) -> float:
    """Score conversational quality and personalization."""
    agent_messages = [m["message"] for m in conversation_history if m["role"] == "agent"]
    if not agent_messages:
        return 0.0

    prospect_name = task_config["prospect_profile"]["visible"]["name"].split()[0].lower()
    company = task_config["prospect_profile"]["visible"]["company"].lower()
    industry = task_config["prospect_profile"]["visible"]["industry"].lower()

    score = 0.0

    # 1. Used prospect's name at least once (0.25)
    if any(prospect_name in m.lower() for m in agent_messages):
        score += 0.25

    # 2. Referenced company or industry (0.25)
    if any(
        company in m.lower() or any(w in m.lower() for w in industry.split() if len(w) > 3)
        for m in agent_messages
    ):
        score += 0.25

    # 3. Asked before pitching — first 3 messages should contain questions (0.25)
    early_messages = agent_messages[:3]
    questions_early = sum(1 for m in early_messages if "?" in m)
    if questions_early >= 2:
        score += 0.25
    elif questions_early >= 1:
        score += 0.125

    # 4. No monologues — no single message over 200 words (0.25)
    monologues = sum(1 for m in agent_messages if len(m.split()) > 200)
    if monologues == 0:
        score += 0.25
    elif monologues <= 1:
        score += 0.125

    return min(1.0, score)


def score_objection_handling(conversation_history: list, task_config: dict) -> float:
    """Score how well the agent addressed the prospect's objections."""
    objections = task_config["prospect_profile"]["hidden"].get("objections", [])
    if not objections:
        return 1.0  # No objections to handle (e.g. Task 4)

    empathy_keywords = [
        "understand", "hear you", "makes sense", "appreciate", "valid", "fair point",
        "i get that", "that's a great", "good question", "absolutely", "right",
    ]

    handled_count = 0.0
    raised_count = 0

    for objection in objections:
        obj_keywords = [w for w in objection.lower().split() if len(w) > 3]
        if not obj_keywords:
            continue

        # Check if prospect raised this objection
        for i, msg in enumerate(conversation_history):
            if msg["role"] != "prospect":
                continue
            if not any(kw in msg["message"].lower() for kw in obj_keywords):
                continue

            raised_count += 1

            # Check next 2 agent messages for acknowledgment
            next_agent_msgs = [
                conversation_history[j]["message"]
                for j in range(i + 1, min(i + 4, len(conversation_history)))
                if conversation_history[j]["role"] == "agent"
            ][:2]

            for agent_msg in next_agent_msgs:
                has_empathy = any(ew in agent_msg.lower() for ew in empathy_keywords)
                has_substance = (
                    any(kw in agent_msg.lower() for kw in obj_keywords)
                    or len(agent_msg.split()) > 20
                )
                if has_empathy and has_substance:
                    handled_count += 1
                    break
                elif has_empathy or has_substance:
                    handled_count += 0.5
                    break
            break  # Only count first instance of each objection

    if raised_count == 0:
        return 0.5  # Neutral — objections weren't triggered

    return min(1.0, handled_count / raised_count)


def score_outcome(
    conversation_history: list,
    task_config: dict,
    agent_final_action: str,
    emotional_state: EmotionalState,
) -> float:
    """Score whether the agent achieved the task's win condition."""
    win_condition = task_config["win_condition"]

    if win_condition == "book_meeting":
        last_prospect_msgs = [
            m["message"] for m in conversation_history[-4:] if m["role"] == "prospect"
        ]
        all_prospect_text = " ".join(last_prospect_msgs).lower()

        positive_signals = [
            "sure", "let's do it", "sounds good", "book", "schedule", "set up",
            "send me", "i'm in", "let's go ahead", "next week", "calendar",
            "meeting", "demo", "follow up", "yes",
        ]
        negative_signals = [
            "no thanks", "not interested", "pass", "don't think so", "gotta go",
            "maybe later", "i'll think about it", "send me some info",
        ]

        if any(pos in all_prospect_text for pos in positive_signals):
            if agent_final_action in ["close_attempt", "book_meeting"]:
                return 1.0
            return 0.7  # Prospect willing but agent didn't explicitly close

        if any(neg in all_prospect_text for neg in negative_signals):
            return 0.2  # Soft rejection — at least tried

        return 0.1  # No clear outcome

    elif win_condition == "disqualify":
        if agent_final_action == "disqualify":
            turns_taken = len([m for m in conversation_history if m["role"] == "agent"])
            if turns_taken <= 8:
                return 1.0   # Fast disqualification
            elif turns_taken <= 12:
                return 0.8
            else:
                return 0.6   # Very slow to realize

        elif agent_final_action in ["close_attempt", "book_meeting"]:
            return 0.0  # Tried to close a bad lead — worst outcome

        return 0.15  # Ended without clear action

    return 0.0


def compute_final_score(
    conversation_history: list,
    task_config: dict,
    agent_final_action: str,
    emotional_state: EmotionalState,
) -> dict:
    """Compute the final episode score across all four dimensions."""
    discovery = score_discovery(conversation_history, task_config)
    rapport = score_rapport(conversation_history, task_config)
    objection = score_objection_handling(conversation_history, task_config)
    outcome = score_outcome(conversation_history, task_config, agent_final_action, emotional_state)

    # Clamp all sub-scores
    discovery = max(0.0, min(1.0, discovery))
    rapport = max(0.0, min(1.0, rapport))
    objection = max(0.0, min(1.0, objection))
    outcome = max(0.0, min(1.0, outcome))

    weights = {
        "discovery": 0.25,
        "rapport": 0.15,
        "objection_handling": 0.25,
        "outcome": 0.35,
    }

    final = (
        discovery * weights["discovery"]
        + rapport * weights["rapport"]
        + objection * weights["objection_handling"]
        + outcome * weights["outcome"]
    )

    final = max(0.0, min(1.0, final))

    return {
        "final_score": round(final, 4),
        "breakdown": {
            "discovery": round(discovery, 4),
            "rapport": round(rapport, 4),
            "objection_handling": round(objection, 4),
            "outcome": round(outcome, 4),
        },
        "weights": weights,
    }
