# phone-relay-agent

A local, API-key-free language relay agent for phone-call interpreting: English <-> French.

The other side's speech is spoken aloud (French) with English subtitles; your reply is
spoken in French. The relay lives in the browser — no call tap, no recording, nothing
left the machine.

## Run

    python relay_agent.py            # 127.0.0.1:8767
    python relay_agent.py --lan      # 0.0.0.0 so the phone on the same Wi-Fi can connect
    python relay_agent.py --port 9000

Then open `http://127.0.0.1:8767` (or the LAN IP on the same Wi-Fi). A one-shot demo
walks a French caller speaking, with English subtitles and a French voice reply.

## Endpoints

- `GET /` — the UI
- `GET /api/languages` — supported codes (en, fr)
- `GET /api/demo-fr` — 6 pre-scripted French caller phrases + English translations
- `GET /api/translate?text=...&from=en&to=fr` — EN->FR
- `GET /api/translate?text=...&from=fr&to=en` — FR->EN

Translation backend: MyMemory (free, keyless, CORS-enabled). Speech: browser speechSynthesis
(fr-FR voice on the French side).

## Model

- `relay_agent.py` — stdlib server + translator + live-mic hooks (no pip, no keys)
- `relay.html` — phone-first dark UI, demo + live-mic modes, subtitle panels, disclosure

## Real calls

A real phone call needs a telephony platform (Twilio / Vonage / SIP / French operator
app). This prototype covers the relay loop and live mic; the call-media bridge is a
separate integration phase.

## Privacy

Binds to 127.0.0.1 by default; `--lan` exposes the same loop to the local Wi-Fi only.
Nothing is recorded — the loop is in memory only.
