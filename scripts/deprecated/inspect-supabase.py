#!/usr/bin/env python3
"""Supabase contact_requests Tabelle inspizieren."""

import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))

import httpx
from src.config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("SUPABASE_URL oder SUPABASE_SERVICE_ROLE_KEY nicht gesetzt!")
    sys.exit(1)

headers = {
    "apikey": SUPABASE_SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
}

# Tabellen-Schema abfragen via OpenAPI
print("=== Tabellen-Info ===")
r = httpx.get(f"{SUPABASE_URL}/rest/v1/contact_requests?select=*&limit=0", headers=headers)
print(f"Status: {r.status_code}")
print(f"Content-Range: {r.headers.get('content-range', 'N/A')}")

# Spalten via OpenAPI spec
print("\n=== OpenAPI Schema ===")
r2 = httpx.get(f"{SUPABASE_URL}/rest/v1/", headers=headers)
if r2.status_code == 200:
    spec = r2.json()
    if "definitions" in spec and "contact_requests" in spec["definitions"]:
        table_def = spec["definitions"]["contact_requests"]
        props = table_def.get("properties", {})
        required = table_def.get("required", [])
        print(f"Spalten ({len(props)}):")
        for col, info in props.items():
            req_marker = " [REQUIRED]" if col in required else ""
            desc = info.get("description", "")
            fmt = info.get("format", info.get("type", "?"))
            print(f"  - {col}: {fmt}{req_marker} {desc}")
    else:
        available = list(spec.get("definitions", {}).keys())
        print(f"Tabelle 'contact_requests' nicht gefunden. Verfügbar: {available}")
else:
    print(f"OpenAPI Fehler: {r2.status_code}")

# Erste paar Einträge
print("\n=== Vorhandene Einträge (max 5) ===")
r3 = httpx.get(
    f"{SUPABASE_URL}/rest/v1/contact_requests?select=*&limit=5&order=created_at.desc",
    headers=headers,
)
if r3.status_code == 200:
    rows = r3.json()
    if rows:
        for row in rows:
            print(row)
    else:
        print("Tabelle ist leer.")
else:
    print(f"Fehler: {r3.status_code} — {r3.text}")
