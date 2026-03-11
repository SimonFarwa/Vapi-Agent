#!/usr/bin/env python3
"""Supabase Storage-Diagnose: Findet heraus, was den Speicher frisst."""

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


print("=" * 60)
print("SUPABASE STORAGE DIAGNOSE")
print(f"URL: {SUPABASE_URL}")
print("=" * 60)

# 1. Alle Tabellen aus dem OpenAPI Schema holen
print("\n--- 1. Alle Tabellen (public schema via OpenAPI) ---")
r = httpx.get(f"{SUPABASE_URL}/rest/v1/", headers=headers, timeout=15)
tables = []
if r.status_code == 200:
    spec = r.json()
    defs = spec.get("definitions", {})
    tables = list(defs.keys())
    print(f"  Gefundene Tabellen: {len(tables)}")
    for t in sorted(tables):
        cols = defs[t].get("properties", {})
        print(f"    - {t} ({len(cols)} Spalten)")
else:
    print(f"  Fehler: {r.status_code} — {r.text[:300]}")

# 2. Zeilenanzahl pro Tabelle
print("\n--- 2. Zeilenanzahl pro Tabelle ---")
for t in sorted(tables):
    r = httpx.get(
        f"{SUPABASE_URL}/rest/v1/{t}?select=*",
        headers={**headers, "Prefer": "count=exact", "Range": "0-0"},
        timeout=15,
    )
    content_range = r.headers.get("content-range", "?")
    # content-range format: "0-0/total" or "*/0" for empty
    total = content_range.split("/")[-1] if "/" in content_range else "?"
    print(f"  {t}: {total} Zeilen (Content-Range: {content_range})")

# 3. Storage Buckets
print("\n--- 3. Storage Buckets ---")
r = httpx.get(f"{SUPABASE_URL}/storage/v1/bucket", headers=headers, timeout=15)
if r.status_code == 200:
    buckets = r.json()
    if not buckets:
        print("  Keine Storage Buckets vorhanden.")
    for b in buckets:
        bucket_id = b.get("id", "?")
        bucket_name = b.get("name", "?")
        public = b.get("public", False)
        created = b.get("created_at", "?")
        print(f"\n  Bucket: {bucket_name} (id={bucket_id}, public={public})")
        print(f"    Erstellt: {created}")

        # Dateien im Bucket auflisten
        r2 = httpx.post(
            f"{SUPABASE_URL}/storage/v1/object/list/{bucket_id}",
            headers={**headers, "Content-Type": "application/json"},
            json={"prefix": "", "limit": 1000, "offset": 0},
            timeout=30,
        )
        if r2.status_code == 200:
            objects = r2.json()
            total_size = 0
            file_count = 0
            for obj in objects:
                meta = obj.get("metadata", {})
                if meta:
                    size = meta.get("size", 0)
                    total_size += size
                    file_count += 1
                elif obj.get("name"):
                    # Könnte ein Ordner sein — rekursiv listen
                    folder_name = obj["name"]
                    r3 = httpx.post(
                        f"{SUPABASE_URL}/storage/v1/object/list/{bucket_id}",
                        headers={**headers, "Content-Type": "application/json"},
                        json={"prefix": folder_name, "limit": 1000, "offset": 0},
                        timeout=30,
                    )
                    if r3.status_code == 200:
                        sub_objects = r3.json()
                        for sobj in sub_objects:
                            smeta = sobj.get("metadata", {})
                            if smeta:
                                size = smeta.get("size", 0)
                                total_size += size
                                file_count += 1

            size_mb = total_size / (1024 * 1024)
            print(f"    Dateien: {file_count}")
            print(f"    Größe: {size_mb:.2f} MB ({total_size:,} bytes)")

            # Top 10 größte Dateien
            if objects:
                files_with_size = []
                for obj in objects:
                    meta = obj.get("metadata", {})
                    if meta and meta.get("size"):
                        files_with_size.append((obj.get("name", "?"), meta["size"], meta.get("mimetype", "?")))
                files_with_size.sort(key=lambda x: x[1], reverse=True)
                if files_with_size:
                    print(f"    Top {min(10, len(files_with_size))} größte Dateien:")
                    for name, size, mime in files_with_size[:10]:
                        print(f"      {name}: {size / 1024:.1f} KB ({mime})")
        else:
            print(f"    Fehler beim Listen: {r2.status_code} — {r2.text[:200]}")
else:
    print(f"  Fehler: {r.status_code} — {r.text[:300]}")

# 4. Prüfe ob es eine Supabase Realtime Subscription gibt
print("\n--- 4. Auth Users (Anzahl) ---")
r = httpx.get(
    f"{SUPABASE_URL}/auth/v1/admin/users?page=1&per_page=1",
    headers=headers,
    timeout=15,
)
if r.status_code == 200:
    data = r.json()
    total = data.get("total", "?") if isinstance(data, dict) else len(data)
    print(f"  Auth Users: {total}")
else:
    print(f"  Fehler: {r.status_code} — {r.text[:200]}")

# 5. Versuche pg_stat_statements über RPC (falls Funktion existiert)
print("\n--- 5. Datenbank-Info via RPC ---")
# Teste ob eine custom function existiert
for func_name in ["get_db_size", "db_size", "pg_database_size"]:
    r = httpx.post(
        f"{SUPABASE_URL}/rest/v1/rpc/{func_name}",
        headers={**headers, "Content-Type": "application/json"},
        json={},
        timeout=10,
    )
    if r.status_code == 200:
        print(f"  {func_name}: {r.json()}")

# 6. Versuche die Tabellengröße via einer RPC function zu bekommen
# Erstmal schauen ob es custom functions gibt
print("\n--- 6. Verfügbare RPC Functions ---")
r = httpx.get(f"{SUPABASE_URL}/rest/v1/rpc/", headers=headers, timeout=15)
if r.status_code == 200:
    print(f"  Response: {str(r.json())[:500]}")
else:
    # Try OpenAPI paths
    r2 = httpx.get(f"{SUPABASE_URL}/rest/v1/", headers=headers, timeout=15)
    if r2.status_code == 200:
        spec = r2.json()
        paths = spec.get("paths", {})
        rpc_funcs = [p.replace("/rpc/", "") for p in paths if "/rpc/" in p]
        print(f"  RPC Functions: {rpc_funcs if rpc_funcs else 'Keine gefunden'}")

print("\n" + "=" * 60)
print("DIAGNOSE ABGESCHLOSSEN")
print("=" * 60)
