import logging
from fastapi import APIRouter, Request
from fastapi.responses import Response

from app import config

logger = logging.getLogger(__name__)

router = APIRouter()


@router.api_route("/voice", methods=["GET", "POST"])
async def voice_webhook(request: Request):
    """Return TwiML that opens a bidirectional Media Stream."""
    ngrok_url = config.NGROK_URL
    # Convert https:// to wss:// for WebSocket
    ws_url = ngrok_url.replace("https://", "wss://").replace("http://", "ws://")

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="{ws_url}/ws" />
    </Connect>
</Response>"""

    logger.info("TwiML served, streaming to %s/ws", ws_url)
    return Response(content=twiml, media_type="application/xml")


@router.post("/status")
async def status_callback(request: Request):
    """Receive call status updates from Twilio."""
    form = await request.form()
    status = form.get("CallStatus", "unknown")
    call_sid = form.get("CallSid", "unknown")
    logger.info("Call %s status: %s", call_sid, status)
    return {"status": "ok"}
