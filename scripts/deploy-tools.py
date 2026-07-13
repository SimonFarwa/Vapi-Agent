#!/usr/bin/env python3
"""Deployed die Tool-Definitionen aus config/tools/ zur Vapi API.

Jede JSON-Datei mit einem "id"-Feld wird per PATCH /tool/:id gepusht.
Dateien ohne "id" werden übersprungen (mit Warnung).

Usage:
    python scripts/deploy-tools.py            # Deploy alle Tools
    python scripts/deploy-tools.py --verify   # Nur GET + Vergleich, kein PATCH
"""

import json
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import VAPI_API_KEY, VAPI_BASE_URL

TOOLS_DIR = Path(__file__).parent.parent / "config" / "tools"

# Fields the Vapi API does not accept in PATCH requests
READONLY_FIELDS = {"id", "orgId", "createdAt", "updatedAt", "type"}


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json",
    }


def deploy_tool(path: Path, verify_only: bool) -> None:
    config = json.loads(path.read_text())
    tool_id = config.get("id")
    name = config.get("function", {}).get("name", path.stem)
    if not tool_id:
        print(f"SKIP  {path.name}: kein 'id'-Feld")
        return

    if verify_only:
        resp = httpx.get(f"{VAPI_BASE_URL}/tool/{tool_id}", headers=_headers(), timeout=30)
        resp.raise_for_status()
        remote = resp.json()
        print(f"VERIFY {name} ({tool_id[:8]}…): async={remote.get('async')}, "
              f"server={remote.get('server', {}).get('url', 'FEHLT')}, "
              f"messages={[m.get('type') for m in remote.get('messages', [])]}")
        return

    payload = {k: v for k, v in config.items() if k not in READONLY_FIELDS}
    resp = httpx.patch(
        f"{VAPI_BASE_URL}/tool/{tool_id}", headers=_headers(), json=payload, timeout=30
    )
    resp.raise_for_status()
    remote = resp.json()
    print(f"OK    {name} ({tool_id[:8]}…): async={remote.get('async')}, "
          f"server={remote.get('server', {}).get('url', 'FEHLT')}, "
          f"messages={[m.get('type') for m in remote.get('messages', [])]}")


def main() -> None:
    verify_only = "--verify" in sys.argv
    for path in sorted(TOOLS_DIR.glob("*.json")):
        deploy_tool(path, verify_only)


if __name__ == "__main__":
    main()
