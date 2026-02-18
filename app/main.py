import asyncio
import logging

from fastapi import FastAPI, WebSocket

from app.telephony.twilio_webhook import router as twilio_router
from app.telephony.media_stream import handle_media_stream

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="VoiceBot - AI Agent Tester")

# Mount Twilio HTTP routes
app.include_router(twilio_router)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Bidirectional WebSocket endpoint for Twilio Media Streams."""
    await handle_media_stream(websocket)


@app.get("/health")
async def health_check():
    """Verify the server is running."""
    return {"status": "ok", "service": "voicebot"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
