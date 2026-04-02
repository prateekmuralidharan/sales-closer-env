from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class Action:
    """What the sales agent sends each turn."""
    message: str                         # The agent's spoken message
    action_type: str = "message"         # "message" | "close_attempt" | "book_meeting" | "disqualify"


@dataclass
class Observation:
    """What the agent sees after each turn."""
    prospect_message: str                # What the prospect said
    turn_number: int                     # Current turn (1-indexed)
    max_turns: int                       # Max allowed turns for this task
    task_id: str                         # Which task is active
    product_brief: dict                  # Product being sold (name, features, pricing, ICP)
    prospect_brief: dict                 # Visible prospect info (name, company, role, industry)
    conversation_history: List[dict]     # List of {"role": "agent"|"prospect", "message": str}
    task_description: str                # What the agent should try to accomplish
    done: bool = False                   # Whether the episode has ended
    termination_reason: str = ""         # Why the episode ended (if done)
