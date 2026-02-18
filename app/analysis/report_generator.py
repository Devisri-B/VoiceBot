import json
import os
import time
import logging

from app import config
from app.analysis.transcript_logger import format_transcript_text

logger = logging.getLogger(__name__)


def generate_report(transcript: dict, findings: list[dict], scenario: dict) -> dict:
    """Generate a structured analysis report for a single call."""
    report = {
        "scenario_id": scenario["id"],
        "scenario_name": scenario["name"],
        "patient_name": scenario["patient_name"],
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "call_duration_seconds": transcript.get("duration_seconds", 0),
        "turn_count": transcript.get("turn_count", 0),
        "findings": findings,
        "summary": {
            "total_bugs": len(findings),
            "critical": sum(1 for f in findings if f.get("severity") == "critical"),
            "high": sum(1 for f in findings if f.get("severity") == "high"),
            "medium": sum(1 for f in findings if f.get("severity") == "medium"),
            "low": sum(1 for f in findings if f.get("severity") == "low"),
        },
        "transcript_text": format_transcript_text(transcript),
    }
    return report


def save_report(report: dict, scenario_id: str) -> str:
    """Save a report as JSON. Returns the file path."""
    os.makedirs(config.REPORTS_DIR, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"report_{scenario_id}_{timestamp}.json"
    filepath = os.path.join(config.REPORTS_DIR, filename)

    with open(filepath, "w") as f:
        json.dump(report, f, indent=2, default=str)

    logger.info("Report saved: %s", filepath)
    return filepath


def format_bug_report(reports: list[dict]) -> str:
    """Format multiple reports into a human-readable bug report document."""
    lines = [
        "# Bug Report - AI Agent Voice Bot Testing",
        f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"Total scenarios tested: {len(reports)}",
        "",
    ]

    all_findings = []
    for report in reports:
        all_findings.extend(report.get("findings", []))

    total = len(all_findings)
    critical = sum(1 for f in all_findings if f.get("severity") == "critical")
    high = sum(1 for f in all_findings if f.get("severity") == "high")

    lines.append(f"## Summary: {total} issues found ({critical} critical, {high} high)")
    lines.append("")

    for report in reports:
        findings = report.get("findings", [])
        lines.append(f"### Scenario: {report['scenario_name']}")
        lines.append(f"- Patient: {report['patient_name']}")
        lines.append(f"- Duration: {report['call_duration_seconds']:.1f}s")
        lines.append(f"- Issues: {len(findings)}")
        lines.append("")

        if not findings:
            lines.append("No issues found.")
        else:
            for i, finding in enumerate(findings, 1):
                severity = finding.get("severity", "unknown").upper()
                ftype = finding.get("type", "unknown")
                reason = finding.get("reason", "No details")
                lines.append(f"**{i}. [{severity}] {ftype}**")
                lines.append(f"   {reason}")

                if "text" in finding:
                    lines.append(f'   > Agent said: "{finding["text"]}"')
                if "patient_said" in finding:
                    lines.append(f'   > Patient said: "{finding["patient_said"]}"')
                lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)
