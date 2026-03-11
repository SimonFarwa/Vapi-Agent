#!/usr/bin/env python3
"""Deployed die lokale Config zum Vapi Assistant.

Usage:
    python scripts/deploy.py          # Deploy production (assistant.json)
    python scripts/deploy.py --dev    # Deploy dev (dev-assistant.json)
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.vapi.client import update_assistant

CONFIG_DIR = Path(__file__).parent.parent / "config"
PROMPT_PATH = CONFIG_DIR / "system-prompt.md"
ANALYSIS_PATH = CONFIG_DIR / "analysis-plan.json"

# Fields that Vapi API does not accept in PATCH requests (read-only)
READONLY_FIELDS = {"id", "orgId", "createdAt", "updatedAt", "isServerUrlSecretSet"}


def build_payload(config_path: Path) -> dict:
    config = json.loads(config_path.read_text())

    if PROMPT_PATH.exists():
        prompt = PROMPT_PATH.read_text().strip()
        if "model" in config:
            config["model"]["messages"] = [
                {"role": "system", "content": prompt}
            ]

    if ANALYSIS_PATH.exists():
        analysis = json.loads(ANALYSIS_PATH.read_text())
        config["analysisPlan"] = analysis

    # Strip read-only fields before sending to API
    for field in READONLY_FIELDS:
        config.pop(field, None)

    return config


def main():
    is_dev = "--dev" in sys.argv
    config_path = CONFIG_DIR / ("dev-assistant.json" if is_dev else "assistant.json")
    env_label = "DEV" if is_dev else "PRODUCTION"

    # Read assistant ID from config before stripping read-only fields
    raw_config = json.loads(config_path.read_text())
    assistant_id = raw_config.get("id")

    payload = build_payload(config_path)
    print(f"Deploying {env_label} config to Vapi (ID: {assistant_id})...")
    result = update_assistant(payload, assistant_id=assistant_id)
    print(f"Updated: {result.get('name', 'N/A')}")
    print(f"ID: {result.get('id', 'N/A')}")


if __name__ == "__main__":
    main()
