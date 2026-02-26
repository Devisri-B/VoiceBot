import logging
from signalwire.rest import Client

from app import config

logger = logging.getLogger(__name__)


def make_call(webhook_url: str) -> str:
    """Initiate an outbound call via SignalWire REST API.

    Returns the Call SID.
    """
    client = Client(
        config.SIGNALWIRE_PROJECT_ID,
        config.SIGNALWIRE_API_TOKEN,
        signalwire_space_url=config.SIGNALWIRE_SPACE_URL,
    )

    call = client.calls.create(
        to=config.TARGET_PHONE_NUMBER,
        from_=config.SIGNALWIRE_FROM_NUMBER,
        url=f"{webhook_url}/voice",
        status_callback=f"{webhook_url}/status",
        status_callback_event=["initiated", "ringing", "answered", "completed"],
        timeout=30,
    )

    logger.info("Call initiated: SID=%s to=%s", call.sid, config.TARGET_PHONE_NUMBER)
    return call.sid
