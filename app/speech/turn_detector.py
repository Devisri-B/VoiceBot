import time
from enum import Enum


class TurnState(Enum):
    WAITING_FOR_TRIAL_END = "waiting_for_trial_end"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    FINISHED = "finished"


class TurnDetector:
    """Detects conversation turn boundaries using VAD + silence timing."""

    def __init__(self, silence_threshold_ms: int = 700, min_speech_ms: int = 300):
        self.silence_threshold_ms = silence_threshold_ms
        self.min_speech_ms = min_speech_ms
        self.state = TurnState.WAITING_FOR_TRIAL_END

        self._speech_started_at: float | None = None
        self._silence_started_at: float | None = None
        self._has_heard_speech = False

    def on_vad_result(self, is_speech: bool, timestamp_ms: float) -> TurnState:
        """Process a VAD result and return the current turn state."""
        if self.state in (TurnState.WAITING_FOR_TRIAL_END, TurnState.FINISHED):
            return self.state

        if is_speech:
            if not self._has_heard_speech:
                self._speech_started_at = timestamp_ms
                self._has_heard_speech = True
            self._silence_started_at = None

            # Agent interrupted us while we were speaking
            if self.state == TurnState.SPEAKING:
                self.state = TurnState.LISTENING
            elif self.state != TurnState.PROCESSING:
                self.state = TurnState.LISTENING
            return self.state

        # Silence detected
        if self._has_heard_speech and self.state == TurnState.LISTENING:
            if self._silence_started_at is None:
                self._silence_started_at = timestamp_ms

            speech_dur = timestamp_ms - (self._speech_started_at or timestamp_ms)
            silence_dur = timestamp_ms - self._silence_started_at

            if speech_dur >= self.min_speech_ms and silence_dur >= self.silence_threshold_ms:
                self._has_heard_speech = False
                self._silence_started_at = None
                self._speech_started_at = None
                self.state = TurnState.PROCESSING
                return self.state

        return self.state

    def mark_trial_ended(self):
        self.state = TurnState.LISTENING

    def mark_speaking(self):
        self.state = TurnState.SPEAKING
        self._has_heard_speech = False
        self._silence_started_at = None
        self._speech_started_at = None

    def mark_listening(self):
        self.state = TurnState.LISTENING
        self._has_heard_speech = False
        self._silence_started_at = None
        self._speech_started_at = None

    def mark_finished(self):
        self.state = TurnState.FINISHED
