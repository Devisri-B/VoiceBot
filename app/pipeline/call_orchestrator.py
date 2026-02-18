import asyncio
import logging

from app.telephony.twilio_call import make_call
from app.telephony.media_stream import (
    set_scenario,
    get_call_complete_event,
    get_last_transcript,
)
from app.analysis.bug_detector import BugDetector
from app.analysis.report_generator import generate_report, save_report
from app import config

logger = logging.getLogger(__name__)


async def run_call(scenario: dict, webhook_url: str) -> dict | None:
    """Execute a single test call for a given scenario.

    1. Set the scenario for the media stream handler
    2. Initiate the outbound call via Twilio
    3. Wait for the call and media stream to complete
    4. Analyze the transcript for bugs
    5. Generate and save a report

    Returns the analysis report dict, or None if the call failed.
    """
    logger.info("=" * 60)
    logger.info("Starting scenario: %s (%s)", scenario["name"], scenario["id"])
    logger.info("=" * 60)

    # Set scenario for the WebSocket handler
    set_scenario(scenario)

    # Initiate the call
    try:
        call_sid = make_call(webhook_url)
        logger.info("Call SID: %s", call_sid)
    except Exception as e:
        logger.error("Failed to initiate call: %s", e)
        return None

    # Wait for the call to complete
    complete_event = get_call_complete_event()
    if complete_event:
        try:
            await asyncio.wait_for(complete_event.wait(), timeout=config.MAX_CALL_DURATION_S + 30)
        except asyncio.TimeoutError:
            logger.warning("Call timed out waiting for completion")

    # Get the transcript
    transcript = get_last_transcript()
    if not transcript or transcript.get("turn_count", 0) == 0:
        logger.warning("No transcript available for scenario %s", scenario["id"])
        return None

    # Analyze for bugs
    logger.info("Analyzing transcript for bugs...")
    detector = BugDetector()
    findings = detector.analyze(transcript, scenario)

    # LLM-based review
    try:
        llm_findings = await detector.llm_review(transcript, scenario)
        findings.extend(llm_findings)
    except Exception as e:
        logger.warning("LLM review failed: %s", e)

    # Generate report
    report = generate_report(transcript, findings, scenario)
    save_report(report, scenario["id"])

    bug_count = len(findings)
    critical = sum(1 for f in findings if f.get("severity") == "critical")
    logger.info(
        "Scenario %s complete: %d bugs found (%d critical)",
        scenario["id"], bug_count, critical,
    )

    return report
