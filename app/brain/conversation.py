import time


class Conversation:
    """Tracks the full conversation history for a single call."""

    def __init__(self, scenario_id: str):
        self.scenario_id = scenario_id
        self.turns: list[dict] = []
        self.messages: list[dict] = []  # Ollama message format
        self.started_at = time.time()

    def add_agent_utterance(self, text: str, timestamp: float | None = None):
        ts = timestamp or time.time()
        self.turns.append({
            "speaker": "agent",
            "text": text,
            "timestamp": ts,
            "elapsed": round(ts - self.started_at, 2),
        })
        self.messages.append({"role": "user", "content": text})

    def add_patient_utterance(self, text: str, timestamp: float | None = None):
        ts = timestamp or time.time()
        self.turns.append({
            "speaker": "patient",
            "text": text,
            "timestamp": ts,
            "elapsed": round(ts - self.started_at, 2),
        })
        self.messages.append({"role": "assistant", "content": text})

    def get_recent_messages(self, max_turns: int = 10) -> list[dict]:
        return self.messages[-max_turns:]

    def to_transcript(self) -> dict:
        return {
            "scenario_id": self.scenario_id,
            "started_at": self.started_at,
            "duration_seconds": round(time.time() - self.started_at, 2),
            "turn_count": len(self.turns),
            "turns": self.turns,
        }
