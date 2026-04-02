"""
SalesCloserEnvironment — Core environment logic.

Lifecycle:
  POST /reset?task_id=warm_lead
    → Loads task config, initializes emotional state, returns opening observation
  POST /step {action: {message: "...", action_type: "message"}}
    → Updates emotional state, generates prospect reply via LLM, computes reward
  GET /state
    → Returns current episode metadata

Episode ends when:
  - max_turns reached
  - prospect ends call (patience depleted / dealbreaker)
  - agent sends action_type "close_attempt", "book_meeting", or "disqualify"
"""
import uuid
from copy import deepcopy
from dataclasses import asdict

from server.state_tracker import EmotionalState, update_state
from server.prospect_engine import generate_prospect_reply
from server.grader import compute_final_score
from tasks import ALL_TASKS

TERMINAL_ACTION_TYPES = {"close_attempt", "book_meeting", "disqualify"}


class SalesCloserEnvironment:
    """OpenEnv-compatible environment for B2B sales call simulation."""

    def __init__(self):
        self.episode_id: str = ""
        self.task_config: dict = {}
        self.emotional_state: EmotionalState = EmotionalState()
        self.conversation_history: list = []
        self.step_count: int = 0
        self.done: bool = False
        self.last_action_type: str = "message"

    # ------------------------------------------------------------------
    # reset
    # ------------------------------------------------------------------
    def reset(self, task_id: str = "warm_lead") -> dict:
        task_id = task_id or "warm_lead"
        if task_id not in ALL_TASKS:
            task_id = "warm_lead"

        self.episode_id = str(uuid.uuid4())
        self.task_config = deepcopy(ALL_TASKS[task_id])
        self.emotional_state = EmotionalState(
            patience=self.task_config["personality"]["patience_level"],
        )
        self.conversation_history = []
        self.step_count = 0
        self.done = False
        self.last_action_type = "message"

        # Opening line from the prospect
        opening_line = self.task_config["personality"]["opening_line"]
        self.conversation_history.append({"role": "prospect", "message": opening_line})

        observation = self._build_observation(opening_line)
        return {"observation": observation, "state": self._get_state()}

    # ------------------------------------------------------------------
    # step
    # ------------------------------------------------------------------
    def step(self, action: dict) -> dict:
        if self.done:
            return {
                "observation": self._build_observation(""),
                "reward": 0.0,
                "done": True,
                "state": self._get_state(),
            }

        agent_message = (action.get("message") or "").strip()
        action_type = action.get("action_type", "message")
        if action_type not in {"message", "close_attempt", "book_meeting", "disqualify"}:
            action_type = "message"

        self.last_action_type = action_type
        self.step_count += 1

        # Append agent message
        self.conversation_history.append({"role": "agent", "message": agent_message})

        # Update emotional state (deterministic)
        old_trust = self.emotional_state.trust
        self.emotional_state = update_state(
            self.emotional_state,
            agent_message,
            self.task_config,
            self.step_count,
        )
        new_trust = self.emotional_state.trust

        # Check termination conditions
        max_turns = self.task_config["max_turns"]
        turn_number = self.step_count

        terminal = (
            action_type in TERMINAL_ACTION_TYPES
            or self.emotional_state.prospect_ended_call
            or turn_number >= max_turns
        )

        if terminal:
            self.done = True

            # Generate a final prospect reply (unless prospect already ended)
            prospect_reply = ""
            if not self.emotional_state.prospect_ended_call and agent_message:
                try:
                    prospect_reply = generate_prospect_reply(
                        self.task_config,
                        self.emotional_state,
                        self.conversation_history,
                    )
                    self.conversation_history.append(
                        {"role": "prospect", "message": prospect_reply}
                    )
                except Exception:
                    prospect_reply = "I appreciate your time. Let me think about this."

            # Compute final score
            score_result = compute_final_score(
                self.conversation_history,
                self.task_config,
                action_type,
                self.emotional_state,
            )
            reward = score_result["final_score"]

            termination_reason = self._get_termination_reason(action_type)
            observation = self._build_observation(
                prospect_reply,
                done=True,
                termination_reason=termination_reason,
                score_breakdown=score_result,
            )

            return {
                "observation": observation,
                "reward": reward,
                "done": True,
                "state": self._get_state(),
            }

        # Not terminal — generate prospect reply
        prospect_reply = ""
        try:
            prospect_reply = generate_prospect_reply(
                self.task_config,
                self.emotional_state,
                self.conversation_history,
            )
        except Exception:
            prospect_reply = "Could you tell me more about that?"

        self.conversation_history.append({"role": "prospect", "message": prospect_reply})

        # Shaping reward: trust delta
        reward = round((new_trust - old_trust) * 0.1, 4)

        observation = self._build_observation(prospect_reply)
        return {
            "observation": observation,
            "reward": reward,
            "done": False,
            "state": self._get_state(),
        }

    # ------------------------------------------------------------------
    # state
    # ------------------------------------------------------------------
    def get_state(self) -> dict:
        return self._get_state()

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _build_observation(
        self,
        prospect_message: str,
        done: bool = False,
        termination_reason: str = "",
        score_breakdown: dict = None,
    ) -> dict:
        visible = self.task_config.get("prospect_profile", {}).get("visible", {})
        product = self.task_config.get("product", {})

        obs = {
            "prospect_message": prospect_message,
            "turn_number": self.step_count,
            "max_turns": self.task_config.get("max_turns", 18),
            "task_id": self.task_config.get("task_id", ""),
            "product_brief": product,
            "prospect_brief": visible,
            "conversation_history": list(self.conversation_history),
            "task_description": self.task_config.get("task_description", ""),
            "done": done,
            "termination_reason": termination_reason,
        }
        if score_breakdown:
            obs["score_breakdown"] = score_breakdown
        return obs

    def _get_state(self) -> dict:
        return {
            "episode_id": self.episode_id,
            "step_count": self.step_count,
            "task_id": self.task_config.get("task_id", ""),
            "turn_number": self.step_count,
            "done": self.done,
        }

    def _get_termination_reason(self, action_type: str) -> str:
        if action_type in TERMINAL_ACTION_TYPES:
            return f"agent_action:{action_type}"
        if self.emotional_state.dealbreaker_triggered:
            return "dealbreaker_triggered"
        if self.emotional_state.prospect_ended_call:
            return "prospect_ended_call"
        if self.step_count >= self.task_config.get("max_turns", 18):
            return "max_turns_reached"
        return "unknown"
