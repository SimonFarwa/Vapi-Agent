#!/usr/bin/env python3
"""Holt den aktuellen Assistant-Stand von Vapi und speichert ihn lokal."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.vapi.client import get_assistant

CONFIG_PATH = Path(__file__).parent.parent / "config" / "assistant.json"


def main():
    # Try to get assistant ID from existing config first
    assistant_id = None
    if CONFIG_PATH.exists():
        try:
            existing = json.loads(CONFIG_PATH.read_text())
            assistant_id = existing.get("id")
        except (json.JSONDecodeError, KeyError):
            pass

    print(f"Fetching assistant from Vapi (ID: {assistant_id or 'from .env'})...")
    data = get_assistant(assistant_id=assistant_id)
    CONFIG_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"Gespeichert: {CONFIG_PATH}")
    print(f"Name: {data.get('name', 'N/A')}")
    print(f"ID: {data.get('id', 'N/A')}")
    print(f"Model: {data.get('model', {}).get('model', 'N/A')}")


if __name__ == "__main__":
    main()
