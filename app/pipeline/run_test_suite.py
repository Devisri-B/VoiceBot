import asyncio
import argparse
import logging
import sys
import json
import os

from app.scenarios.loader import load_all_scenarios, load_scenario
from app.pipeline.call_orchestrator import run_call
from app import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def run_test_suite(
    scenario_ids: list[str] | None = None,
    delay_between_calls: int = 10,
):
    """Run multiple test call scenarios sequentially.

    Args:
        scenario_ids: Specific scenario IDs to run. None = run all.
        delay_between_calls: Seconds to wait between calls.
    """
    if scenario_ids:
        scenarios = [load_scenario(sid) for sid in scenario_ids]
    else:
        scenarios = load_all_scenarios()

    webhook_url = config.NGROK_URL
    if not webhook_url:
        logger.error("NGROK_URL not set. Start ngrok and set the URL in .env")
        return

    logger.info("Running %d scenarios against %s", len(scenarios), config.TARGET_PHONE_NUMBER)
    logger.info("Webhook URL: %s", webhook_url)

    results = []

    for i, scenario in enumerate(scenarios):
        logger.info("\n[%d/%d] Scenario: %s", i + 1, len(scenarios), scenario["name"])

        report = await run_call(scenario, webhook_url)
        results.append({
            "scenario_id": scenario["id"],
            "scenario_name": scenario["name"],
            "success": report is not None,
            "bugs_found": len(report.get("findings", [])) if report else 0,
            "report": report,
        })

        # Wait between calls to not overwhelm the system
        if i < len(scenarios) - 1:
            logger.info("Waiting %ds before next call...", delay_between_calls)
            await asyncio.sleep(delay_between_calls)

    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUITE SUMMARY")
    print("=" * 60)

    total_bugs = 0
    for r in results:
        status = "OK" if r["success"] else "FAILED"
        bugs = r["bugs_found"]
        total_bugs += bugs
        print(f"  [{status}] {r['scenario_name']}: {bugs} bugs found")

    print(f"\nTotal: {len(results)} calls, {total_bugs} bugs found")
    print("Transcripts saved to: output/transcripts/")
    print("Reports saved to: output/reports/")

    # Save summary
    summary_path = os.path.join(config.REPORTS_DIR, "summary.json")
    os.makedirs(config.REPORTS_DIR, exist_ok=True)
    with open(summary_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Summary saved to: {summary_path}")


def main():
    parser = argparse.ArgumentParser(description="Run voice bot test suite")
    parser.add_argument(
        "--scenario", "-s",
        type=str,
        help="Run a specific scenario by ID (e.g., schedule_new). Omit to run all.",
    )
    parser.add_argument(
        "--delay", "-d",
        type=int,
        default=10,
        help="Seconds between calls (default: 10)",
    )
    args = parser.parse_args()

    scenario_ids = [args.scenario] if args.scenario else None
    asyncio.run(run_test_suite(scenario_ids=scenario_ids, delay_between_calls=args.delay))


if __name__ == "__main__":
    main()
