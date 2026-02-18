import os
import yaml
import logging

from app import config

logger = logging.getLogger(__name__)


def load_scenario(scenario_id: str) -> dict:
    """Load a single scenario by ID from the definitions directory."""
    definitions_dir = config.SCENARIOS_DIR
    for filename in os.listdir(definitions_dir):
        if not filename.endswith(".yaml"):
            continue
        filepath = os.path.join(definitions_dir, filename)
        with open(filepath) as f:
            scenario = yaml.safe_load(f)
        if scenario.get("id") == scenario_id:
            return scenario
    raise ValueError(f"Scenario not found: {scenario_id}")


def load_all_scenarios() -> list[dict]:
    """Load all scenario YAML files, sorted by filename."""
    definitions_dir = config.SCENARIOS_DIR
    scenarios = []
    for filename in sorted(os.listdir(definitions_dir)):
        if not filename.endswith(".yaml"):
            continue
        filepath = os.path.join(definitions_dir, filename)
        with open(filepath) as f:
            scenario = yaml.safe_load(f)
        scenarios.append(scenario)
    logger.info("Loaded %d scenarios", len(scenarios))
    return scenarios


def list_scenario_ids() -> list[str]:
    """Return a list of all scenario IDs."""
    return [s["id"] for s in load_all_scenarios()]
