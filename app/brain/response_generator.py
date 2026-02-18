import asyncio
import logging
import random

from app.brain.llm_client import OllamaClient
from app.brain.patient_persona import build_system_prompt

logger = logging.getLogger(__name__)

FALLBACK_RESPONSES = [
    "I'm sorry, could you repeat that?",
    "Um, one moment, let me think about that.",
    "Sorry, I didn't quite catch that.",
]


class ResponseGenerator:
    """Generates patient responses using Ollama."""

    def __init__(self, scenario: dict):
        self.scenario = scenario
        self.system_prompt = build_system_prompt(scenario)
        self.llm = OllamaClient()
        self.opening_delivered = False

    async def get_opening_line(self) -> str:
        """Generate the first thing the patient says after the agent greets."""
        if not self.opening_delivered:
            self.opening_delivered = True
            messages = [
                {
                    "role": "user",
                    "content": (
                        "The medical office AI just answered the phone. "
                        "What do you say first? Remember to stay in character."
                    ),
                }
            ]
            try:
                return await asyncio.wait_for(
                    self.llm.generate(self.system_prompt, messages),
                    timeout=10.0,
                )
            except (asyncio.TimeoutError, Exception) as e:
                logger.warning("Opening line generation failed: %s", e)
                return f"Hi, my name is {self.scenario['patient_name']}. {self.scenario['goal']}."

    async def generate_response(self, conversation_messages: list[dict]) -> str:
        """Generate a patient response given conversation history."""
        try:
            response = await asyncio.wait_for(
                self.llm.generate(self.system_prompt, conversation_messages),
                timeout=10.0,
            )
            return response.strip()
        except asyncio.TimeoutError:
            logger.warning("LLM timed out, using fallback")
            return random.choice(FALLBACK_RESPONSES)
        except Exception as e:
            logger.error("LLM error: %s", e)
            return random.choice(FALLBACK_RESPONSES)

    async def close(self):
        await self.llm.close()
