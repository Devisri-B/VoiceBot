import json
import os
import time
import logging

from app import config

logger = logging.getLogger(__name__)


def save_transcript(transcript: dict, scenario_id: str) -> str:
    """Save a call transcript as a JSON file. Returns the file path."""
    os.makedirs(config.TRANSCRIPTS_DIR, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"{scenario_id}_{timestamp}.json"
    filepath = os.path.join(config.TRANSCRIPTS_DIR, filename)

    with open(filepath, "w") as f:
        json.dump(transcript, f, indent=2, default=str)

    logger.info("Transcript saved: %s", filepath)
    return filepath


def format_transcript_text(transcript: dict) -> str:
    """Format a transcript as human-readable text."""
    lines = [
        f"Scenario: {transcript['scenario_id']}",
        f"Duration: {transcript['duration_seconds']:.1f}s",
        f"Turns: {transcript['turn_count']}",
        "-" * 50,
    ]

    for turn in transcript["turns"]:
        speaker = "AGENT" if turn["speaker"] == "agent" else "PATIENT"
        elapsed = turn.get("elapsed", 0)
        lines.append(f"[{elapsed:6.1f}s] {speaker}: {turn['text']}")

    return "\n".join(lines)
