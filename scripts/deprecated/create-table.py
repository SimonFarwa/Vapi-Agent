#!/usr/bin/env python3
"""Erstellt die voice_agent_contacts Tabelle in Supabase."""

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
    "Content-Type": "application/json",
    "Prefer": "return=minimal",
}

SQL = """
CREATE TABLE IF NOT EXISTS voice_agent_contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT now(),
    first_name TEXT,
    last_name TEXT,
    email TEXT,
    phone TEXT,
    caller_number TEXT,
    concern TEXT,
    call_id TEXT,
    status TEXT DEFAULT 'new',
    source TEXT DEFAULT 'voice_agent'
);

-- RLS aktivieren
ALTER TABLE voice_agent_contacts ENABLE ROW LEVEL SECURITY;

-- Policy: Service Role hat vollen Zugriff
CREATE POLICY "service_role_full_access" ON voice_agent_contacts
    FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- Index auf call_id fuer schnelle Lookups
CREATE INDEX IF NOT EXISTS idx_voice_agent_contacts_call_id
    ON voice_agent_contacts(call_id);

-- Index auf created_at fuer zeitbasierte Abfragen
CREATE INDEX IF NOT EXISTS idx_voice_agent_contacts_created_at
    ON voice_agent_contacts(created_at DESC);
"""

print("Erstelle Tabelle 'voice_agent_contacts'...")
r = httpx.post(
    f"{SUPABASE_URL}/rest/v1/rpc/",
    headers=headers,
    json={"query": SQL},
)

# Fallback: SQL via pg_net oder direkt via SQL endpoint
if r.status_code != 200:
    print(f"RPC fehlgeschlagen ({r.status_code}), versuche SQL-Endpoint...")
    # Supabase SQL endpoint (nur mit service_role key)
    r2 = httpx.post(
        f"{SUPABASE_URL}/pg/query",
        headers={
            "apikey": SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": "application/json",
        },
        json={"query": SQL},
    )
    if r2.status_code in (200, 201):
        print("Tabelle erfolgreich erstellt!")
        print(r2.json() if r2.text else "OK")
    else:
        print(f"SQL-Endpoint auch fehlgeschlagen ({r2.status_code}): {r2.text}")
        print("\n--- Manueller Fallback ---")
        print("Führe dieses SQL manuell im Supabase SQL Editor aus:")
        print(SQL)
else:
    print("Tabelle erfolgreich erstellt!")

# Verifizieren
print("\n=== Verifizierung ===")
r3 = httpx.get(f"{SUPABASE_URL}/rest/v1/", headers=headers)
if r3.status_code == 200:
    spec = r3.json()
    if "definitions" in spec and "voice_agent_contacts" in spec["definitions"]:
        table_def = spec["definitions"]["voice_agent_contacts"]
        props = table_def.get("properties", {})
        print(f"Tabelle 'voice_agent_contacts' gefunden mit {len(props)} Spalten:")
        for col, info in props.items():
            fmt = info.get("format", info.get("type", "?"))
            print(f"  - {col}: {fmt}")
    else:
        print("Tabelle noch nicht sichtbar im Schema. Evtl. manuell erstellen.")
