#!/usr/bin/env python3
"""Vergleicht lokale Config mit dem aktuellen Stand auf Vapi."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.vapi.client import get_assistant

CONFIG_PATH = Path(__file__).parent.parent / "config" / "assistant.json"


def deep_diff(local: dict, remote: dict, path: str = "") -> list[str]:
    diffs = []
    all_keys = set(list(local.keys()) + list(remote.keys()))

    for key in sorted(all_keys):
        current_path = f"{path}.{key}" if path else key
        local_val = local.get(key)
        remote_val = remote.get(key)

        if local_val == remote_val:
            continue

        if isinstance(local_val, dict) and isinstance(remote_val, dict):
            diffs.extend(deep_diff(local_val, remote_val, current_path))
        else:
            diffs.append(
                f"  {current_path}:\n"
                f"    lokal:  {json.dumps(local_val, ensure_ascii=False)[:120]}\n"
                f"    remote: {json.dumps(remote_val, ensure_ascii=False)[:120]}"
            )

    return diffs


def main():
    if not CONFIG_PATH.exists():
        print("Keine lokale Config. Erst `python scripts/fetch.py` ausführen.")
        sys.exit(1)

    local = json.loads(CONFIG_PATH.read_text())
    remote = get_assistant()

    diffs = deep_diff(local, remote)
    if not diffs:
        print("Keine Unterschiede. Lokal und remote sind identisch.")
    else:
        print(f"{len(diffs)} Unterschiede gefunden:\n")
        print("\n".join(diffs))


if __name__ == "__main__":
    main()
