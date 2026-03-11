#!/usr/bin/env python3
"""Deployed die lokale Config zum Vapi Assistant."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.vapi.client import update_assistant

CONFIG_PATH = Path(__file__).parent.parent / "config" / "assistant.json"
PROMPT_PATH = Path(__file__).parent.parent / "config" / "system-prompt.md"
ANALYSIS_PATH = Path(__file__).parent.parent / "config" / "analysis-plan.json"


def build_payload() -> dict:
    config = json.loads(CONFIG_PATH.read_text())

    if PROMPT_PATH.exists():
        prompt = PROMPT_PATH.read_text().strip()
        if "model" in config:
            config["model"]["messages"] = [
                {"role": "system", "content": prompt}
            ]

    if ANALYSIS_PATH.exists():
        analysis = json.loads(ANALYSIS_PATH.read_text())
        config["analysisPlan"] = analysis

    return config


def main():
    payload = build_payload()
    print("Deploying assistant config to Vapi...")
    result = update_assistant(payload)
    print(f"Updated: {result.get('name', 'N/A')}")
    print(f"ID: {result.get('id', 'N/A')}")


if __name__ == "__main__":
    main()
