# Vapi-Agent (Irene) — Projektgedächtnis

> Oben **Aktueller Stand** (lebendig), darunter **Änderungslog** (neueste oben, Datum + Uhrzeit). Neue Sessions lesen zuerst hier. **Keine Secrets** (git-Datei).

## Aktueller Stand (2026-07-13)

Voice-Agent "Irene" (Config-as-Code, `config/assistant.json` = Source of Truth, `scripts/deploy.py` pusht per REST). Rezeptionistin für Farpa, geht an die 08272 1819444, bucht Beratungstermine mit Simon. Assistant-ID `4e057623-…`.

**Aktueller Stack (deployed 2026-07-12):** LLM `gpt-5.2-chat-latest` (temp 0.2, maxTokens 256), Transcriber Deepgram `flux-general-multi` (Deutsch, native End-of-Turn, `eotThreshold 0.7` / `eotTimeoutMs 1200`), TTS ElevenLabs `eleven_flash_v2_5` (voiceId unverändert). 3 Tools über n8n (`save_customer_info`, `check_available_slots`, `book_appointment`).

**Privacy (Simons Vorgabe):** `artifactPlan` = kein Audio/Video/PCAP, aber `transcriptPlan.enabled: true` → Transkript + Auswertung fließen per `end-of-call-report` an n8n → Hermes (Ablage pro Kundin). Kein Audio wird gespeichert.

**Offen:** Simon muss einen Testanruf machen (Verifikation nach Deploy). Optional später: LLM auf `gemini-2.5-flash` (schnellste TTFT) oder Mistral (EU) testen — nur nach Tool-Calling-Test. Ein einzelner Assistant reicht (kein Squad).

**Altlasten bereinigt:** Supabase-Scripts nach `scripts/deprecated/`. CLAUDE.md nennt Supabase/WAT-Framework noch — inhaltlich veraltet, Details siehe hier.

## Änderungslog

### 2026-07-12 20:00 CEST — Stack-Upgrade + Altlasten-Fix + Deploy
- endCallMessage + metadata.companyName "Architekturbüro zwo P" (Vor-Kunde) → Farpa; Transcriber-Keywords von Handwerker- auf Kosmetik-Vokabular.
- Transcriber `nova-3` → `flux-general-multi`, TTS `eleven_turbo_v2_5` → `eleven_flash_v2_5`, `smartEndpointingPlan` entfernt (Flux macht End-of-Turn nativ), 2s künstliche Latenz raus (responseDelay/llmRequestDelay 0), stopSpeakingPlan.numWords 2.
- `artifactPlan` privacy-hart (recording/video/pcap false, transcriptPlan.enabled true).
- Verbotene Garantien ("Geld zurück", "Zahlung bei Fertigstellung") aus Prod- + Dev-Prompt entfernt, KI-Offenlegung (EU AI Act Art. 50) + 4. Service in den Prompt.
- Supabase-Scripts nach `scripts/deprecated/`. Deployed via `deploy.py`, `fetch.py`-verifiziert (lokal == remote), gepusht.
- **Wichtig:** Die 3 Tools laufen über n8n-Workflow `Vapi Server Handler` (voqWTtrJbgMw3Mlu). Dort wurden am selben Tag zwei kaputte Funktionen gefixt (Terminbuchung/Slot-Abfrage lagen wegen n8n-Security-Restriktion brach). Details: `/root/hermes-agent/edit.md`.
