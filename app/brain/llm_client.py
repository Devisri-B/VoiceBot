import json
import httpx

from app import config


class OllamaClient:
    """HTTP client for the Ollama local LLM."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
    ):
        self.base_url = base_url or config.OLLAMA_BASE_URL
        self.model = model or config.OLLAMA_MODEL
        self.client = httpx.AsyncClient(timeout=30.0)

    async def generate(self, system_prompt: str, messages: list[dict]) -> str:
        """Generate a response from Ollama (non-streaming)."""
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                *messages,
            ],
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 80,
                "top_p": 0.9,
            },
        }

        response = await self.client.post(
            f"{self.base_url}/api/chat",
            json=payload,
        )
        response.raise_for_status()
        return response.json()["message"]["content"]

    async def generate_streaming(self, system_prompt: str, messages: list[dict]):
        """Yield tokens as they arrive for lower latency."""
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                *messages,
            ],
            "stream": True,
            "options": {
                "temperature": 0.7,
                "num_predict": 80,
                "top_p": 0.9,
            },
        }

        async with self.client.stream(
            "POST", f"{self.base_url}/api/chat", json=payload
        ) as response:
            async for line in response.aiter_lines():
                if not line.strip():
                    continue
                data = json.loads(line)
                if not data.get("done"):
                    yield data["message"]["content"]

    async def close(self):
        await self.client.aclose()
