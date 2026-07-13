# Vapi-Agent (Irene) — Projektgedächtnis

> Oben **Aktueller Stand** (lebendig), darunter **Änderungslog** (neueste oben, Datum + Uhrzeit). Neue Sessions lesen zuerst hier. **Keine Secrets** (git-Datei).

## Aktueller Stand (2026-07-13)

Voice-Agent "Irene" (Config-as-Code, `config/assistant.json` = Source of Truth, `scripts/deploy.py` pusht per REST). Rezeptionistin für Farpa, geht an die 08272 1819444, bucht Beratungstermine mit Simon. Assistant-ID `4e057623-…`.

**Aktueller Stack (deployed 2026-07-13):** LLM `gpt-5.2-chat-latest` (temp 0.2, maxTokens 256), Transcriber Deepgram `flux-general-multi` (Deutsch, native End-of-Turn, `eotThreshold 0.7` / `eotTimeoutMs 1200`), TTS ElevenLabs `eleven_flash_v2_5` (voiceId unverändert). **Tool-Verkabelung (2026-07-13 repariert):** 4 Tools = `save_customer_info` (Fallback auf assistant.server.url), `end_call_tool`, `check_available_slots` (`5492c3c9…`), `book_appointment` (`2d746ab1…`). Alle Daten-Tools laufen jetzt über den n8n-Handler `Vapi Server Handler` (`/webhook/vapi-server`), der Kontakt→Hermes + cal.com Slots/Buchung macht. `assistant.server.url` = `/webhook/vapi-server` (auch für End-of-Call-Report→Hermes).

**Privacy (Simons Vorgabe):** `artifactPlan` = kein Audio/Video/PCAP, aber `transcriptPlan.enabled: true` → Transkript + Auswertung fließen per `end-of-call-report` an n8n → Hermes (Ablage pro Kundin). Kein Audio wird gespeichert.

**Offen:** (1) Echter Testanruf durch Simon an 08272 1819444 — finale Bestätigung, dass Vapi die Tool-Args im erwarteten Format schickt (E2E-Sim + Zeitzone schon grün). (2) Aussprache „Stengelmair" (TTS, Phase 2, empirisch). (3) Vapi-Key rotieren (im Chat exponiert). Optional später: LLM auf `gemini-2.5-flash`/Mistral testen. Ein einzelner Assistant reicht (kein Squad).

**Altlasten bereinigt:** Supabase-Scripts nach `scripts/deprecated/`. CLAUDE.md nennt Supabase/WAT-Framework noch — inhaltlich veraltet, Details siehe hier.

## Änderungslog

### 2026-07-13 11:59 CEST — Terminbuchung repariert: Tool-Verkabelung auf Webhook-Handler umgehängt
- **Was:** Testanruf-Analyse (Call `019f580d…`, 2026-07-12 22:38): Irene sagte 2× „Einen Moment…" und legte auf. Root Cause (REST + Vapi-MCP doppelt verifiziert): `save_customer_info` hatte leere `server.url` → Fallback auf `assistant.server.url` = tote `…/mcp-test/c95a47f5…`-TEST-URL → `No result returned`. Das `n8n_tool` (mcp) zeigte auf toten `…/mcp/f3bfbf4a…`-Endpunkt. `check_available_slots`/`book_appointment` existierten gar nicht als Tools. Der aktive `Vapi Server Handler` (`/webhook/vapi-server`) wurde von keinem Vapi-Tool aufgerufen. Nebenbefund: auch `end-of-call-report` ging an die tote URL → Hermes-Ablage kam nie an.
- **Fix (Webhook-Design, Simons Wahl):** (1) Zwei Function-Tools `check_available_slots` (`5492c3c9…`) + `book_appointment` (`2d746ab1…`) in Vapi angelegt, `server.url` explizit = `/webhook/vapi-server`, Param-Namen exakt passend zu den Handler-Code-Nodes (`startTime`/`endTime` bzw. `start`/`firstName`/`lastName`/`email`/`phone`/`notes`). Als config-as-code unter `config/tools/` abgelegt. (2) `assistant.server.url` → `/webhook/vapi-server` (fixt Tool-Fallback **und** End-of-Call-Report in einem). (3) Totes `n8n_tool` aus `toolIds` raus. `toolIds` jetzt = `[save_customer_info, end_call_tool, check_available_slots, book_appointment]`.
- **Verifiziert:** `diff.py` zeigte nur die 2 gewollten Änderungen, `deploy.py` + `fetch.py` bestätigt (server.url + toolIds remote korrekt). E2E-Simulation (POST tool-call an `/webhook/vapi-server`): liefert korrektes Vapi-Format `{results:[{toolCallId, result}]}` mit echten cal.com-Slots. **Offen:** echter Testanruf durch Simon (finale Bestätigung des Vapi-Tool-Call-Formats).
- **Wichtig entdeckt:** Der offizielle **Vapi MCP Server** ist jetzt installiert (User-Scope, `mcp.vapi.ai/mcp`) — kann lesen + `create_tool`/`update_tool`/`update_assistant`. Der Vapi-Key wurde im Chat im Klartext gezeigt → **rotieren empfohlen**.
- **Zeitzone gefixt (direkt danach):** cal.com `/slots/available` gab Zeiten in **UTC** (`…Z`) zurück, weil der Node keinen `timeZone`-Param schickte — Irene hätte 2h zu früh angesagt. Fix: Query-Param `timeZone=Europe/Berlin` an den Node „Cal.com Check Slots" (Workflow `voqWTtrJbgMw3Mlu`); cal.com rechnet jetzt selbst um (DST-sicher). Verifiziert: Webhook liefert `…+02:00` statt `…Z`. Booking-Node hat `attendee.timeZone=Europe/Berlin` → Buchung passt. (n8n-Änderung ist nicht in diesem Repo.)
- **Noch offen:** Aussprache „Stengelmair" (TTS, Phase 2, empirisch). Nebenbei: cal.com-Verfügbarkeit zeigt 09:00-Slots, obwohl der Prompt „Mo-Do 10-16" behauptet — Prompt-Zeiten vs. echte cal.com-Availability mal abgleichen.

### 2026-07-12 20:00 CEST — Stack-Upgrade + Altlasten-Fix + Deploy
- endCallMessage + metadata.companyName "Architekturbüro zwo P" (Vor-Kunde) → Farpa; Transcriber-Keywords von Handwerker- auf Kosmetik-Vokabular.
- Transcriber `nova-3` → `flux-general-multi`, TTS `eleven_turbo_v2_5` → `eleven_flash_v2_5`, `smartEndpointingPlan` entfernt (Flux macht End-of-Turn nativ), 2s künstliche Latenz raus (responseDelay/llmRequestDelay 0), stopSpeakingPlan.numWords 2.
- `artifactPlan` privacy-hart (recording/video/pcap false, transcriptPlan.enabled true).
- Verbotene Garantien ("Geld zurück", "Zahlung bei Fertigstellung") aus Prod- + Dev-Prompt entfernt, KI-Offenlegung (EU AI Act Art. 50) + 4. Service in den Prompt.
- Supabase-Scripts nach `scripts/deprecated/`. Deployed via `deploy.py`, `fetch.py`-verifiziert (lokal == remote), gepusht.
- **Wichtig:** Die 3 Tools laufen über n8n-Workflow `Vapi Server Handler` (voqWTtrJbgMw3Mlu). Dort wurden am selben Tag zwei kaputte Funktionen gefixt (Terminbuchung/Slot-Abfrage lagen wegen n8n-Security-Restriktion brach). Details: `/root/hermes-agent/edit.md`.
